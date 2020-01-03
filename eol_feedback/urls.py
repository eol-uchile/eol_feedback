from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolFeedbackFragmentView, update_feedback, set_visibility
from django.contrib.auth.decorators import login_required


urlpatterns = (
       url(
           r'courses/{}/student_feedback$'.format(
               settings.COURSE_ID_PATTERN,
           ),
           EolFeedbackFragmentView.as_view(),
           name='feedback_view',
       ),
       url(
           r'student_feedback/update',
           login_required(update_feedback),
           name='feedback_post_update',
       ),
       url(
           r'student_feedback/set_visibility',
           login_required(set_visibility),
           name='feedback_post_set_visibility',
       ),
   )