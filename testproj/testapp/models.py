from django.db import models

from auth_media import AuthFileField


class MediaModel(models.Model):
    interim_media = AuthFileField(upload_to="interim")
    xaccel_media = AuthFileField(upload_to="xaccel", media_server='xaccel')
    secure_media = AuthFileField(upload_to="secure", media_server='secure')
