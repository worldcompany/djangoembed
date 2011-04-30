import os
from setuptools import setup, find_packages

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()

setup(
    name='djangoembed',
    version='0.1.1',
    description='rich media consuming/providing for django',
    long_description=readme,
    author='Charles Leifer',
    author_email='coleifer@gmail.com',
    url='http://github.com/worldcompany/djangoembed/tree/master',
    packages=find_packages(),
    package_data = {
        'oembed': [
            'fixtures/*.json',
            'templates/*.html',
            'templates/*/*.html',
            'templates/*/*/*.html',
            'tests/fixtures/*.json',
            'tests/templates/*.html',
            'tests/templates/*/*.html',
            'tests/templates/*/*/*.html',
        ],
    },
    install_requires = [
        'PIL',
        'BeautifulSoup',
        'httplib2',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    test_suite='runtests.runtests',
)
