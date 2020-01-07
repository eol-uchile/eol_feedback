# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from nose.tools import assert_true
from mock import patch, Mock


from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse

from util.testing import UrlResetMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory

import views
from models import EolFeedback, SectionVisibility


class TestStaffView(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):

        super(TestStaffView, self).setUp()

        # create a course
        self.course = CourseFactory.create(org='mss', course='999',
                                           display_name='eol feedback course')
        
        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            # Create the student
            self.student = UserFactory(username='student', password='test', email='student@edx.org')
            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Create and Enroll staff user
            self.staff_user = UserFactory(username='staff_user', password='test', email='staff@edx.org', is_staff=True)
            CourseEnrollmentFactory(user=self.staff_user, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert_true(self.client.login(username='student', password='test'))
            
            # Log the user staff in
            self.staff_client = Client()
            assert_true(self.staff_client.login(username='staff_user', password='test'))
        
    '''
    def test_staff_get(self):
        
        response = self.client.get(reverse('feedback_view', kwargs={'course_id' : self.course.location.course_key}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'eol_feedback/eol_feedback_fragment.html')
    '''
    def test_render_page(self):

        url = reverse('feedback_view',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)

    def test_grade_percent_scaled(self):
        # 0.03 <= grade_cutoff <= 0.97
        test_cases = [[.0, .6, 1.], [.4, .4, 4.], [1., .97, 7.], [.7, .6, 4.8], [.3, .6, 2.5]] # [grade_percent, grade_cutoff, grade_scaled]
        for tc in test_cases:
            grade_scaled = views.grade_percent_scaled(tc[0], tc[1])
            self.assertEqual(grade_scaled, tc[2])

    def test_get_feedback(self):
        block_id = 'block_id'
        block_feedback = 'block feedback'
        feedback = EolFeedback.objects.create(
                block_id = block_id,
                block_feedback = block_feedback
            )
        self.assertEqual(views.get_feedback(block_id), block_feedback)

        block_id2 = 'block_does_not_exist'
        block_feedback2 = ''
        self.assertEqual(views.get_feedback(block_id2), block_feedback2)

    def test_get_visibility(self):
        section_id = "section_id"
        course_id = self.course.id.to_deprecated_string()
        is_visible = True
        visibility = SectionVisibility.objects.create(
                section_id = section_id,
                course_id = course_id,
                is_visible = is_visible
            )
        self.assertEqual(views.get_section_visibility(section_id, course_id), True)

        section_id2 = "section_id2"
        is_visible2 = False
        visibility2 = SectionVisibility.objects.create(
                section_id = section_id2,
                course_id = course_id,
                is_visible = is_visible2
            )
        self.assertEqual(views.get_section_visibility(section_id2, course_id), False)
        
        section_id3 = 'sections_does_not_exist'
        self.assertEqual(views.get_section_visibility(section_id3, course_id), False)

    def test_post_update_feedback(self):
        block_id = "block_id"
        block_feedback = "block feedback"
        course_id = self.course.id.to_deprecated_string()
        response = self.client.post(reverse('feedback_post_update'), {'block_id' : block_id, 'block_feedback' : block_feedback, 'course_id' : course_id})
        self.assertEqual(response.status_code, 401) # self.client is not staff

        # post with staff_client
        response2 = self.staff_client.post(reverse('feedback_post_update'), {'block_id' : block_id, 'block_feedback' : block_feedback, 'course_id' : course_id})
        self.assertEqual(response2.status_code, 201) # feedback created

        new_block_feedback = "new block feedback"
        response3 = self.staff_client.post(reverse('feedback_post_update'), {'block_id' : block_id, 'block_feedback' : new_block_feedback, 'course_id' : course_id})
        self.assertEqual(response3.status_code, 200) # feedback updated

    def test_post_set_visibility(self):
        section_id = "section_id"
        course_id = self.course.id.to_deprecated_string()
        response = self.client.post(reverse('feedback_post_set_visibility'), {'section_id' : section_id, 'course_id' : course_id})
        self.assertEqual(response.status_code, 401) # self.client is not staff

        # post with staff_client
        response2 = self.staff_client.post(reverse('feedback_post_set_visibility'), {'section_id' : section_id, 'course_id' : course_id})
        self.assertEqual(response2.status_code, 201) # visibility created

        response3 = self.staff_client.post(reverse('feedback_post_set_visibility'), {'section_id' : section_id, 'course_id' : course_id})
        self.assertEqual(response3.status_code, 200) # visibility updated
        