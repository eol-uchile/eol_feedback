# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from openedx.core.lib.tests.tools import assert_true
from mock import patch, Mock


from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse

from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from capa.tests.response_xml_factory import StringResponseXMLFactory
from lms.djangoapps.courseware.tests.factories import StudentModuleFactory

from lms.djangoapps.grades.tasks import compute_all_grades_for_course as task_compute_all_grades_for_course
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access

from six import text_type
from six.moves import range

import views
from models import EolFeedback, SectionVisibility

USER_COUNT = 11


class TestStaffView(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):
        super(TestStaffView, self).setUp()
        # create a course
        self.course = CourseFactory.create(org='mss', course='999',
                                           display_name='eol feedback course')

        # Now give it some content
        with self.store.bulk_operations(self.course.id, emit_signals=False):
            chapter = ItemFactory.create(
                parent_location=self.course.location,
                category="sequential",
            )
            section = ItemFactory.create(
                parent_location=chapter.location,
                category="sequential",
                metadata={'graded': True, 'format': 'Homework'}
            )
            self.items = [
                ItemFactory.create(
                    parent_location=section.location,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'}
                )
                for __ in range(USER_COUNT - 1)
            ]

        # Create users, enroll and set grades
        self.users = [UserFactory.create() for _ in range(USER_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
        for i, item in enumerate(self.items):
            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1,
                    student=user,
                    course_id=self.course.id,
                    module_state_key=item.location
                )
        task_compute_all_grades_for_course.apply_async(kwargs={'course_key': text_type(self.course.id)})

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

    def test_render_page(self):

        url = reverse('feedback_view',
                      kwargs={'course_id': self.course.id})
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)

    def test_grade_percent_scaled(self):
        # 0.03 <= grade_cutoff <= 0.97
        test_cases = [[.0, .6, 1.], [.4, .4, 4.], [1., .97, 7.], [.7, .6, 4.8], [.3, .6, 2.5]]  # [grade_percent, grade_cutoff, grade_scaled]
        for tc in test_cases:
            grade_scaled = views.grade_percent_scaled(tc[0], tc[1])
            self.assertEqual(grade_scaled, tc[2])

    def test_get_feedback(self):
        block_id = 'block_id'
        block_feedback = 'block feedback'
        feedback = EolFeedback.objects.create(
            block_id=block_id,
            block_feedback=block_feedback
        )
        self.assertEqual(views.get_feedback(block_id), block_feedback)

        block_id2 = 'block_does_not_exist'
        block_feedback2 = ''
        self.assertEqual(views.get_feedback(block_id2), block_feedback2)

    def test_get_visibility(self):
        section_id = "section_id"
        course_id = self.course.id
        is_visible = True
        visibility = SectionVisibility.objects.create(
            section_id=section_id,
            course_id=course_id,
            is_visible=is_visible
        )
        self.assertEqual(views.get_section_visibility(section_id, course_id), True)

        section_id2 = "section_id2"
        is_visible2 = False
        visibility2 = SectionVisibility.objects.create(
            section_id=section_id2,
            course_id=course_id,
            is_visible=is_visible2
        )
        self.assertEqual(views.get_section_visibility(section_id2, course_id), False)

        section_id3 = 'sections_does_not_exist'
        self.assertEqual(views.get_section_visibility(section_id3, course_id), False)

    def test_post_update_feedback(self):
        block_id = "block_id"
        block_feedback = "block feedback"
        course_id = self.course.id
        response = self.client.post(reverse('feedback_post_update'), {'block_id': block_id, 'block_feedback': block_feedback, 'course_id': course_id})
        self.assertEqual(response.status_code, 401)  # self.client is not staff

        # post with staff_client
        response2 = self.staff_client.post(reverse('feedback_post_update'), {'block_id': block_id, 'block_feedback': block_feedback, 'course_id': course_id})
        self.assertEqual(response2.status_code, 201)  # feedback created

        new_block_feedback = "new block feedback"
        response3 = self.staff_client.post(reverse('feedback_post_update'), {'block_id': block_id, 'block_feedback': new_block_feedback, 'course_id': course_id})
        self.assertEqual(response3.status_code, 200)  # feedback updated

    def test_post_set_visibility(self):
        section_id = "section_id"
        course_id = self.course.id
        response = self.client.post(reverse('feedback_post_set_visibility'), {'section_id': section_id, 'course_id': course_id})
        self.assertEqual(response.status_code, 401)  # self.client is not staff

        # post with staff_client
        response2 = self.staff_client.post(reverse('feedback_post_set_visibility'), {'section_id': section_id, 'course_id': course_id})
        self.assertEqual(response2.status_code, 201)  # visibility created

        response3 = self.staff_client.post(reverse('feedback_post_set_visibility'), {'section_id': section_id, 'course_id': course_id})
        self.assertEqual(response3.status_code, 200)  # visibility updated

    def test_get_course_info(self):
        course_key = self.course.id
        course = get_course_with_access(self.student, "load", course_key)
        grade_cutoff, avg_grade, min_grade, max_grade = views._get_course_info(course, course_key)
        self.assertEqual(grade_cutoff, 0.5)
        self.assertEqual(max_grade, 1.1)
