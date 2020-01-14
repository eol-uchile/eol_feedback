# EOL Feedback

![https://github.com/eol-uchile/eol_feedback/actions](https://github.com/eol-uchile/eol_feedback/workflows/Python%20application/badge.svg)

Adding feedback for student exams

## Configurations

LMS Django Admin:

- */admin/site_configuration/siteconfiguration/*
    - **"EOL_FEEDBACK_TAB_ENABLED":true**
- */admin/grades/persistentgradesenabledflag/*
    - Set Flag Enabled
- */admin/grades/coursepersistentgradesflag/*
    - Add course id
    - Set Enable
- */admin/waffle/switch/*
    - Add Switch and set Enable: **grades.assume_zero_grade_if_absent**

If courses already exists:

    > docker-compose exec lms python manage.py lms --settings=tutor.production compute_grades --courses COURSE_ID

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run lms /openedx/requirements/eol_feedback/.github/test.sh


## TO DO:

- [ ] Tab has to be initialized on course creation. In this moment the tab will appear after first changes on Advanced settings.
- [ ] Final grade calculated by percentage of progress. If the student didn't answer a test (or the test is not released) he will have 0% (0.0) and final grade will be affected. See what to do in this case.
