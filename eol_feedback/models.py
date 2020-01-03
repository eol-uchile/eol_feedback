# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class EolFeedback(models.Model):
    block_id = models.CharField(max_length=50, unique=True)
    block_feedback = models.TextField()

    def __str__(self):
        return self.block_id

class SectionVisibility(models.Model):
    section_id = models.CharField(max_length=50)
    course_id = models.CharField(max_length=50)
    is_visible = models.BooleanField(default=False)

    def __str__(self):
        return '%s %s (%s)' % (self.course_id, self.section_id, self.is_visible)