#!/bin/dash

cd /openedx/requirements/eol_feedback/eol_feedback
cp /openedx/edx-platform/setup.cfg .
mkdir test_root
cd test_root/
ln -s /openedx/staticfiles .

cd /openedx/requirements/eol_feedback/eol_feedback
DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest tests.py
