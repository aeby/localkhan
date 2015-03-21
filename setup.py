"""
localkhan
---------

localkhan is a tool to download and distribute
Khan content for offline usage.

Run it
``````

.. code:: bash

    $ localkhan get --lang=es early-math/cc-early-math-counting-topic
     * Downloading topic structure and 345 media files
    $ localkhan serve
     * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

Links
`````

* `documentation <http://localkhan.github.io/khan/>`_

"""
from setuptools import setup

import localkhan

setup(
    name='localkhan',
    version=localkhan.__version__,
    url='http://github.com/aeby/localkhan/',
    license='BSD',
    author='Reto Aebersold',
    author_email='aeby@substyle.ch',
    description='Download and distribute Khan content',
    long_description=__doc__,
    packages=['localkhan'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'requests>=2.5.0',
        'docopt>=0.5.0',
        'schema>=0.3.0',
        'clint>=0.4.0',
        'Flask>=0.10.0'
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
