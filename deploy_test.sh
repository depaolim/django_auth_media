# Disclaimer:
#  too many path assumptions and too little error checks!
#  don't use it, it is only a (dirty) memo for Marco
#
# ... if you know what you are doing:
# workon django_auth_media
# . deploy_test.sh

python setup.py sdist
deactivate
mkvirtualenv test_auth_media
pip install ~/Downloads/Django-1.6.8-py2.py3-none-any.whl
pip install git+https://github.com/depaolim/django_auth_media.git
pip freeze
cp -r ../django_auth_media/testproj/ .
cd testproj/
./manage.py test testapp auth_media
cd ..
pip uninstall django_auth_media -y
pip freeze
cp ../django_auth_media/dist/django-auth-media-0.0.1.tar.gz .
pip install django-auth-media-0.0.1.tar.gz
pip freeze
cd testproj/
./manage.py test testapp auth_media
cd ..
deactivate
cd ..
rm -rf test_auth_media/
rmvirtualenv test_auth_media
