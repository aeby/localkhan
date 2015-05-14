from setuptools import setup, find_packages
from codecs import open
from os import path
import localkhan

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='localkhan',
    version=localkhan.__version__,
    url='http://github.com/aeby/localkhan/',
    license=localkhan.__license__,
    author='Reto Aebersold',
    author_email='aeby@substyle.ch',
    description='Download and distribute Khan content',
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'requests==2.7.0',
        'docopt==0.6.2',
        'schema==0.3.1',
        'clint==0.4.1',
        'Flask==0.10.1',
        'netifaces==0.10.4'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Education'
    ],
    entry_points='''
    [console_scripts]
    localkhan=localkhan.cli:main
    '''
)
