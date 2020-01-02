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

from courseware.access import has_access
from courseware.masquerade import setup_masquerade
from django.db.models import prefetch_related_objects
from openedx.features.course_duration_limits.access import generate_course_expired_fragment

from django.db import transaction
from models import EolFeedback

from django.http import HttpResponse

'''
    TODO:
    - Final grade calculated by percentage of progress. 
        > If the student didn't answer a test (or the test is not released) he will have 0% (0.0) and final grade will be affected. 
        > See what to do in this case.
'''


class EolFeedbackFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        context = self.get_context(request, course_id)
        html = render_to_string('eol_feedback/eol_feedback_fragment.html', context)
        fragment = Fragment(html)
        return fragment

    def get_context(self, request, course_id):
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)

        # Get general info of course
        grade_cutoff, avg_grade, min_grade, max_grade = self.get_course_info(course, course_key)

        # masquerade and student required for preview_menu (admin)
        staff_access = bool(has_access(request.user, 'staff', course))
        masquerade, student = setup_masquerade(request, course_key, staff_access, reset_masquerade_data=True)
        prefetch_related_objects([student], 'groups')
        if request.user.id != student.id:
            # refetch the course as the assumed student
            course = get_course_with_access(student, 'load', course_key, check_if_enrolled=True)
        course_grade = CourseGradeFactory().read(student, course) # Student grades
        courseware_summary = list(course_grade.chapter_grades.values())
        course_expiration_fragment = generate_course_expired_fragment(student, course)

        context = {
            "course": course,
            "avg_grade": avg_grade,
            "min_grade": min_grade,
            "max_grade": max_grade,
            "grade_cutoff": grade_cutoff,
            "supports_preview_menu": True,
            "staff_access": staff_access,
            "masquerade": masquerade,
            "student": student,
            "courseware_summary": courseware_summary,
            "grade_summary": course_grade.summary,
            "course_expiration_fragment": course_expiration_fragment,
            "grade_percent_scaled" : self.grade_percent_scaled,
            "get_feedback" : self.get_feedback,
            "update_url" : request.build_absolute_uri('/')[:-1] + "/student_feedback/update",
        }
        return context

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

    def get_feedback(self, block_id):
        try:
            feedback = EolFeedback.objects.get(block_id=block_id)
            return feedback.block_feedback
        except EolFeedback.DoesNotExist:
            return ''

def update_feedback(request):
    # check method and params
    if request.method != "POST":
        return HttpResponse(status=400)
    if 'block_id' not in request.POST and 'block_feedback' not in request.POST and 'course_id' not in request.POST:
        return HttpResponse(status=400)
    
    # check for access
    course_id = request.POST['course_id']
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    staff_access = bool(has_access(request.user, 'staff', course))
    if not staff_access:
        return HttpResponse(status=401)

    # get or create feedback
    block_id = request.POST['block_id']
    block_feedback = request.POST['block_feedback']
    with transaction.atomic():
        try:
            feedback = EolFeedback.objects.get(block_id=block_id)
            feedback.block_feedback = block_feedback
            feedback.save()
            return HttpResponse(status=200)
        except EolFeedback.DoesNotExist:
            feedback = EolFeedback.objects.create(
                block_id = block_id,
                block_feedback = block_feedback
            )
            return HttpResponse(status=201)