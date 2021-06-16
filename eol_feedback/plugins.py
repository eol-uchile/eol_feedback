from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab
from xmodule.tabs import TabFragmentViewMixin

from django.contrib.auth.models import User


class EolFeedbackTab(TabFragmentViewMixin, EnrolledTab):
    type = 'eol_feedback'
    title = ugettext_noop('Feedback')
    priority = None
    view_name = 'feedback_view'
    fragment_view_name = 'eol_feedback.views.EolFeedbackFragmentView'
    is_hideable = True
    is_default = True
    body_class = 'eol_feedback'
    online_help_token = 'eol_feedback'

    @classmethod
    def is_enabled(cls, course, user=None):
        """
            Check if user is enrolled on course
        """
        if not super(EolFeedbackTab, cls).is_enabled(course, user):
            return False
        return configuration_helpers.get_value('EOL_FEEDBACK_TAB_ENABLED', False)
