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

