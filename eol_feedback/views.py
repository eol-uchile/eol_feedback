# -*- coding: utf-8 -*-


from courseware.courses import get_course_with_access
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from opaque_keys.edx.keys import CourseKey

from django.contrib.auth.models import User
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from django.db.models import Avg, Max, Min, Sum

from courseware.access import has_access
from courseware.masquerade import setup_masquerade
from django.db.models import prefetch_related_objects
from openedx.features.course_duration_limits.access import generate_course_expired_fragment

from django.db import transaction
from .models import EolFeedback, SectionVisibility

from django.http import Http404, HttpResponse
from django.core.cache import cache

from django.urls import reverse


def _get_context(request, course_id):
    """
        Return all course/student/user data
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    # Get general info of course
    grade_cutoff, avg_grade, min_grade, max_grade = _get_course_info(course, course_key)

    # masquerade and student required for preview_menu (admin)
    staff_access = bool(has_access(request.user, 'staff', course))
    masquerade, student = setup_masquerade(request, course_key, staff_access, reset_masquerade_data=True)
    prefetch_related_objects([student], 'groups')
    if request.user.id != student.id:
        # refetch the course as the assumed student
        course = get_course_with_access(student, 'load', course_key, check_if_enrolled=True)
    course_grade = CourseGradeFactory().read(student, course)  # Student grades
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
        "can_masquerade": staff_access,
        "student": student,
        "courseware_summary": courseware_summary,
        "grade_summary": course_grade.summary,
        "course_expiration_fragment": course_expiration_fragment,
        "grade_percent_scaled": grade_percent_scaled,
        "get_section_visibility": get_section_visibility,
        "get_feedback": get_feedback,
        "update_url": reverse('feedback_post_update'),
        "set_visibility_url": reverse('feedback_post_set_visibility'),
    }
    return context


def _get_course_info(course, course_key):
    """
        Calculate grade cutoff, average grade, min grade and max grade of all students enrolled in the course
    """
    data = cache.get("eol_feedback-" + course_key._to_string() + "-course_info")  # cache
    if data is None:
        # Get active students on the course
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
        )

        # Get grade summary
        course_info = PersistentCourseGrade.objects.filter(
            user_id__in = enrolled_students,
            course_id = course_key
        ).aggregate(avg_percent = Avg('percent_grade'), min_percent = Min('percent_grade'), max_percent = Max('percent_grade'))
        avg_grade_percent = course_info.get('avg_percent', 0.)
        min_grade_percent = course_info.get('min_percent', 1.)
        max_grade_percent = course_info.get('max_percent', 0.)

        grade_cutoff = min(course.grade_cutoffs.values())  # Get the min value

        # Convert grade format
        avg_grade = grade_percent_scaled(avg_grade_percent, grade_cutoff) if avg_grade_percent is not None else 1.
        min_grade = grade_percent_scaled(min_grade_percent, grade_cutoff) if min_grade_percent is not None else 1.
        max_grade = grade_percent_scaled(max_grade_percent, grade_cutoff) if max_grade_percent is not None else 1.

        # cache
        data = [grade_cutoff, avg_grade, min_grade, max_grade]
        cache.set("eol_feedback-" + course_key._to_string() + "-course_info", data, 60 * 5)

    return data[0], data[1], data[2], data[3]  # grade_cutoff, avg_grade, min_grade, max_grade


def grade_percent_scaled(grade_percent, grade_cutoff):
    """
        Scale grade percent by grade cutoff. Grade between 1.0 - 7.0
    """
    if grade_percent == 0.:
        return 1.
    if grade_percent < grade_cutoff:
        return round(10. * (3. / grade_cutoff * grade_percent + 1.)) / 10.
    return round((3. / (1. - grade_cutoff) * grade_percent + (7. - (3. / (1. - grade_cutoff)))) * 10.) / 10.


def get_section_visibility(section_id, course_id):
    """
        Return true/false if section is visible.
    """
    try:
        visibility = SectionVisibility.objects.get(section_id=section_id, course_id=course_id)
        return visibility.is_visible
    except SectionVisibility.DoesNotExist:
        return False


def get_feedback(block_id):
    """
        Return feedback text if exist
    """
    try:
        feedback = EolFeedback.objects.get(block_id=block_id)
        return feedback.block_feedback
    except EolFeedback.DoesNotExist:
        return ''


class EolFeedbackFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        if(not self.has_page_access(request.user, course_id)):
            raise Http404()
        context = _get_context(request, course_id)
        html = render_to_string('eol_feedback/eol_feedback_fragment.html', context)
        fragment = Fragment(html)
        return fragment
            

    def has_page_access(self, user, course_id):
        course_key = CourseKey.from_string(course_id)
        return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            pk = user.id
        ).exists()


def update_feedback(request):
    """
        Update or create feedback of block_id by POST Method. Request must have block_id, block_feedback and course_id params.
    """
    # check method and params
    if request.method != "POST":
        return HttpResponse(status=400)
    if 'block_id' not in request.POST or 'block_feedback' not in request.POST or 'course_id' not in request.POST:
        return HttpResponse(status=400)

    # check for access
    course_id = request.POST['course_id']
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    staff_access = bool(has_access(request.user, 'staff', course))
    if not staff_access:
        return HttpResponse(status=401)

    # get (and update) or create feedback
    block_id = request.POST['block_id']
    block_feedback = request.POST['block_feedback']
    try:
        feedback = EolFeedback.objects.get(block_id=block_id)
        feedback.block_feedback = block_feedback.strip()
        feedback.save()
        return HttpResponse(status=200)
    except EolFeedback.DoesNotExist:
        feedback = EolFeedback.objects.create(
            block_id=block_id,
            block_feedback=block_feedback.strip()
        )
        return HttpResponse(status=201)


def set_visibility(request):
    """
        Update or create visibility of section_id by POST Method. Request must have section_id and course_id
    """
    # check method and params
    if request.method != "POST":
        return HttpResponse(status=400)
    if 'section_id' not in request.POST or 'course_id' not in request.POST:
        return HttpResponse(status=400)

    # check for access
    course_id = request.POST['course_id']
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    staff_access = bool(has_access(request.user, 'staff', course))
    if not staff_access:
        return HttpResponse(status=401)

    # change or create visibility
    section_id = request.POST['section_id']
    try:
        visibility = SectionVisibility.objects.get(section_id=section_id, course_id=course_id)
        visibility.is_visible = not visibility.is_visible  # change bool
        visibility.save()
        return HttpResponse(status=200)
    except SectionVisibility.DoesNotExist:
        visibility = SectionVisibility.objects.create(
            section_id=section_id,
            course_id=course_id,
            is_visible=True
        )
        return HttpResponse(status=201)
