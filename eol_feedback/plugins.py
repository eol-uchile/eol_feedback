from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab
import django_comment_client.utils as utils
from xmodule.tabs import TabFragmentViewMixin

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
        return True