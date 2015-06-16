from setuptools import setup, find_packages

CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    author="Marco De Paoli",
    author_email="depaolim@gmail.com",
    name='django-auth-media',
    version='0.0.3',
    description='Django media files: check authorization and serve',
    url='https://github.com/depaolim/django_auth_media',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)
