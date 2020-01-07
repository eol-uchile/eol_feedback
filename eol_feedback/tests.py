# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from nose.tools import assert_true
from mock import patch, Mock


from django.test import TestCase, Client
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
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert_true(self.client.login(username=uname, password=password))
        
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
        course_id = "course_id"
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
        


