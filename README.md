# README

Serving media based on authorization checks

Download the repo:

    git clone https://github.com/depaolim/django_auth_media.git

The app is tested on Django 1.6.7 and has no dependency from other packages (apart from django itself)


## Usage

Steps:

1. Add the folder django\_auth\_media to your PYTHONPATH

2. Use auth\_media.AuthMediaField in place of models.FileField

    from django.db import models
    from auth_media import AuthFileField

    class MediaModel(models.Model):
        media_field = AuthFileField(
            upload_to="media_model_folder",
            permission="testapp.view_mediamodel")

AuthFileField expects the following params:

    * permission: string or callable
        * string specify a permission full-name, or
        * callable with the following parameters (model_instance, request)
     * media_server: server name as defined in settings.MEDIA_SERVERS (see below)

3. Add urlpatterns in urls.py

    import auth_media
    urlpatterns += auth_media.urlpatterns()

4. Add MEDIA\_URL  and MEDIA\_ROOT in settings.py

    MEDIA_URL = '/media/'
    MEDIA_ROOT = 'path_to_files_on_file_system'

5. Define MEDIA\_SERVERS in settings.py

Example:

    MEDIA_SERVERS = {
        'default': {
            'ENGINE': "auth_media.backends.interim",
        },
        'xaccel': {
            'ENGINE': "auth_media.backends.xaccel",
            'REDIRECT': "/internal_media",
        },
        'secure': {
            'ENGINE': "auth_media.backends.secure_link",
            'SECRET': "SUpeRSecREt",
            'REDIRECT': "/secure_media",
        },
    }

If settings.MEDIA\_SERVERS is not defined, default is:

    MEDIA_SERVERS = {
        'default': {
            'ENGINE': "auth_media.backends.interim",
        },
    }

Media servers battery-included in auth\_media package:

    * "interim" slow, should be used only in debug (wrapper for on django.views.static.serve)
    * "xaccel" based on X-Accel-Redirect header as managed by nginx (similar to Apache X-Sendfile)
    * "secure\_link" based on secure\_link mechanism managed by nginx

Engine function must define two positional arguments:

    * request: the current request object
    * path: as returned by property field.name

Other key-value (ex. REDIRECT or SECRET) specified inside each media\_server definition, are used as "named parameters" automatically binded to engine function

It is easy to define new media servers and plug them in auth\_media

If you you define new general-purpose media-servers please let me know and I will be happy to integrate them in auth\_media core

5. "xaccel" configuration

    Use the same path used in "internal location" in nginx config. Example:

    settings.py:

        'xaccel': {
            'ENGINE': "auth_media.backends.xaccel",
            'REDIRECT': "/internal_media",
        },

    nginx.conf:

        location /internal_media {
            internal;
            alias /path_to_media_files;
        }

6. "secure\_link" configuration

    Use the same path used in "rewrite location" in nginx config. Example:

        'secure': {
            'ENGINE': "auth_media.backends.secure_link",
            'SECRET': "SUpeRSecREt",
            'REDIRECT': "/secure_media",
        },

    nginx.conf:

        location /secure_media/ {
            secure_link_secret SUpeRSecREt;

            if ($secure_link = "") {
                return 403;
            }

            rewrite ^ /path_to_media_files/$secure_link;
        }


## Test

To run tests:

    cd testproj
    pip install -r requirements.txt
    python manage.py test testapp auth_media
