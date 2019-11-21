# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from courseware.courses import get_course_with_access
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from opaque_keys.edx.keys import CourseKey

# Create your views here.

"""
def my_custom_function(request, course_id):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    context = {
        "course": course,
    }
    return render_to_response("eol_feedback/eol_feedback_fragment.html", context)

"""
class EolFeedbackFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        context = {
            "course": course,
        }
        html = render_to_string('eol_feedback/eol_feedback_fragment.html', context)
        fragment = Fragment(html)
        return fragment
