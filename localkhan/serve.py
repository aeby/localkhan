# -*- coding: utf-8 -*-
"""
    localkhan.serve
    ~~~~~~~~~~~~~~~
    Serves the content player web app and creates
    the necessary appcache manifest.
    :copyright: (c) 2015 by Reto Aebersold.
    :license: MIT, see LICENSE for more details.
"""
from __future__ import print_function

from localkhan import KHAN_CONTENT_STATIC
import os
from flask import Flask, send_from_directory
from flask import render_template, make_response

app = Flask(__name__)
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

LOCAL_KHAN_PATH = None


def set_khan_base_path(path):
    global LOCAL_KHAN_PATH
    LOCAL_KHAN_PATH = path


def get_manifest():
    global LOCAL_KHAN_PATH

    assets = set()

    for root_dir, dirs, files in os.walk(LOCAL_KHAN_PATH):
        for file_name in files:
            assets.add(os.path.join(KHAN_CONTENT_STATIC, root_dir[len(LOCAL_KHAN_PATH) + 1:], file_name))

    return render_template('lkhan.appcache', assets=assets)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def root(path):
    # calculate manifest entries to show load progress
    start = False
    asset_count = 0
    for line in get_manifest().split('\n'):
        line = line.strip()
        if line == 'CACHE:':
            start = True
        elif line == 'NETWORK:':
            start = False
        elif start and len(line) > 0:
            asset_count += 1

    resp = make_response(render_template('index.html', asset_count=asset_count))
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route('/khan.appcache')
def manifest():
    response = make_response(get_manifest())
    response.headers['Content-Type'] = 'text/cache-manifest'
    response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/static/khan/<path:path>')
def khan_content(path):
    global LOCAL_KHAN_PATH

    if LOCAL_KHAN_PATH is None:
        raise RuntimeError('LOCAL_KHAN_PATH not set.')

    return send_from_directory(LOCAL_KHAN_PATH, path)
