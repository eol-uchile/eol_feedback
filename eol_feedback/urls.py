from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolFeedbackFragmentView, update_feedback
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
   )