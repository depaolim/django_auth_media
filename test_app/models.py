from django.db import models

from auth_media import AuthFileField


class MediaModel(models.Model):
    media_field = AuthFileField(upload_to="media_model_folder")
