# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from courseware.courses import get_course_with_access
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from opaque_keys.edx.keys import CourseKey

from django.contrib.auth.models import User
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from xmodule.modulestore.django import modulestore


class EolFeedbackFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        grade_cutoff, avg_grade, min_grade, max_grade = self.get_course_info(course, course_key)
        context = {
            "course": course,
            "avg_grade": avg_grade,
            "min_grade": min_grade,
            "max_grade": max_grade,
            "grade_cutoff": grade_cutoff
        }
        html = render_to_string('eol_feedback/eol_feedback_fragment.html', context)
        fragment = Fragment(html)
        return fragment

    def get_course_info(self, course, course_key):
        # Get active students on the course
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
        ).order_by('username').select_related("profile")

        total_students = enrolled_students.count()

        # Get grade summary
        with modulestore().bulk_operations(course.location.course_key):
            student_info = [
                {
                    'username': student.username,
                    'id': student.id,
                    'email': student.email,
                    'grade_summary': CourseGradeFactory().read(student, course).summary
                }
                for student in enrolled_students
            ]

        # Calculate average, min and max grades
        avg_grade_percent = 0.
        min_grade_percent = 1.
        max_grade_percent = 0.
        for student in student_info:
            student_grade_percent = student['grade_summary']['percent']
            avg_grade_percent = avg_grade_percent + student_grade_percent
            min_grade_percent = min(student_grade_percent, min_grade_percent)
            max_grade_percent = max(student_grade_percent, max_grade_percent)
        avg_grade_percent = avg_grade_percent / total_students
        grade_cutoff = min(course.grade_cutoffs.values()) # Get the min value

        # Convert grade format
        avg_grade = self.grade_percent_scaled(avg_grade_percent, grade_cutoff)
        min_grade = self.grade_percent_scaled(min_grade_percent, grade_cutoff)
        max_grade = self.grade_percent_scaled(max_grade_percent, grade_cutoff)
        return grade_cutoff, avg_grade, min_grade, max_grade


    def grade_percent_scaled(self, grade_percent, grade_cutoff):
        if grade_percent < grade_cutoff:
            return round(10. * (3. / grade_cutoff * grade_percent + 1.)) / 10.
        return round((3. / (1. - grade_cutoff) * grade_percent + (7. - (3. / (1. - grade_cutoff)))) * 10.) / 10.