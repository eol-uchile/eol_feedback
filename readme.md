*To enable tab, set on site configurations (django admin): **"EOL_FEEDBACK_TAB_ENABLED":true***

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run lms /openedx/requirements/eol_feedback/.github/test.sh


## TO DO:

- [ ] Tab has to be initialized on course creation. In this moment the tab will appear after first changes on Advanced settings.
- [ ] Final grade calculated by percentage of progress. If the student didn't answer a test (or the test is not released) he will have 0% (0.0) and final grade will be affected. See what to do in this case.