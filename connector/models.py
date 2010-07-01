"""
Connector Models

Ben Adida
2010-01-27
"""

from django.db import models
from django.conf import settings

import hashlib, uuid, string, logging

from datetime import datetime

class Connection(models.Model):
  indivo_token = models.CharField(max_length = 50)
  indivo_secret = models.CharField(max_length = 50)
  indivo_record_id = models.CharField(max_length = 50)
  hospital_token = models.CharField(max_length = 50)
  hospital_secret = models.CharField(max_length = 50)
  hospital_record_id = models.CharField(max_length = 50)
  created_at = models.DateTimeField(auto_now_add = True)

