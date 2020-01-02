# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class EolFeedback(models.Model):
    block_id = models.CharField(max_length=50, unique=True)
    block_feedback = models.TextField()

    def __str__(self):
        return self.block_id