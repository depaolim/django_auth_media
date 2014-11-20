from django.db import models

from auth_media import AuthFileField


class MediaModel(models.Model):
    slow_media = AuthFileField(upload_to="slow")
    xaccel_media = AuthFileField(upload_to="xaccel", engine='xaccel')
    secure_media = AuthFileField(upload_to="secure", engine='secure')
