from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolFeedbackFragmentView


urlpatterns = (
       url(
           r'courses/{}/student_feedback$'.format(
               settings.COURSE_ID_PATTERN,
           ),
           EolFeedbackFragmentView.as_view(),
           name='feedback_view',
       ),
   )