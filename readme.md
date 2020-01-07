*To enable tab, set on site configurations (django admin): **"EOL_FEEDBACK_TAB_ENABLED":true***

## TESTS
**Prepare tests:**

    > cd /openedx/requirements/eol_feedback/eol_feedback
    > cp /openedx/edx_platform/setup.cfg .
    > mkdir test_root
    > cp -r /openedx/staticfiles/ ./test_root/

**Run tests**

    > cd /openedx/requirements/eol_feedback/eol_feedback
    > EDXAPP_TEST_MONGO_HOST=mongodb pytest tests.py

## TO DO:

 - [ ] Tab has to be initialized on course creation. In this moment the tab will appear after first changes on Advanced settings.
- [ ] Final grade calculated by percentage of progress. If the student didn't answer a test (or the test is not released) he will have 0% (0.0) and final grade will be affected. See what to do in this case.