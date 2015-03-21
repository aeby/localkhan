# -*- coding: utf-8 -*-
"""
    localkhan.serve
    ~~~~~~~~~~~~~~~
    Serves the content player web app and creates
    the necessary appcache manifest.
    :copyright: (c) 2015 by Reto Aebersold.
    :license: MIT, see LICENSE for more details.
"""

import hashlib

from os.path import normpath, walk, isdir, isfile, dirname, basename, \
    exists as path_exists, join as path_join

from flask import Flask
from flask import render_template, make_response


app = Flask(__name__)


def path_checksum(path):
    """
    Recursively calculates a checksum representing the contents of all files
    found in directory path.

    """

    def _update_checksum(existing_checksum, dir_name, file_names):
        for filename in sorted(file_names):
            file_path = path_join(dir_name, filename)
            if isfile(file_path):
                fh = open(file_path, 'rb')
                while 1:
                    buf = fh.read(4096)
                    if not buf:
                        break
                    existing_checksum.update(buf)
                fh.close()

    checksum = hashlib.sha1()
    path = normpath(path)
    if path_exists(path):
        if isdir(path):
            walk(path, _update_checksum, checksum)
        elif isfile(path):
            _update_checksum(checksum, dirname(path), basename(path))

    return checksum.hexdigest()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def root(path):
    return app.send_static_file('index.html')


@app.route('/khan.appcache')
def manifest():
    assets = [
        'static/cc-early-math-add-sub-topic-data/f3043f4e2d941f4e280b4f4abb3cb89f0a12acbc.png',
        'static/cc-early-math-add-sub-topic-data/ced0ad2c1b9a3a3471e6adedd6c05ac85abb80f4.png'
    ]

    response = make_response(render_template('khan.appcache', assets=assets,
                                             hash=path_checksum(app.static_folder)))
    response.headers['Content-Type'] = 'text/cache-manifest'
    return response
