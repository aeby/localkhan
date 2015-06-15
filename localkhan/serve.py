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
import json

from localkhan import KHAN_CONTENT_STATIC, ASSET_FOLDER
import os
from flask import Flask, send_from_directory
from flask import render_template, make_response

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

LOCAL_KHAN_PATH = None


def set_khan_base_path(path):
    global LOCAL_KHAN_PATH
    LOCAL_KHAN_PATH = path


def get_manifest():
    """
    Creates the cache manifest content based on the asset index.
    :return: manifest file content
    """
    global LOCAL_KHAN_PATH

    assets = []

    content_structure = ['exercises.json', 'topics.json', 'videos.json']
    assets.extend([os.path.join(KHAN_CONTENT_STATIC, a) for a in content_structure])

    assets_file_path = os.path.join(LOCAL_KHAN_PATH, 'assets.json')
    with open(assets_file_path) as assets_file:
        assets.extend(
            [os.path.join(KHAN_CONTENT_STATIC, ASSET_FOLDER, url.split('/')[-1]) for url in json.load(assets_file)])

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

    response = make_response(render_template('index.html', asset_count=asset_count))
    response.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    return response


@app.route('/khan.appcache')
def manifest():
    response = make_response(get_manifest())
    response.headers['Content-Type'] = 'text/cache-manifest'
    response.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    return response


@app.route('/static/khan/<path:path>')
def khan_content(path):
    global LOCAL_KHAN_PATH

    if LOCAL_KHAN_PATH is None:
        raise RuntimeError('LOCAL_KHAN_PATH not set.')

    return send_from_directory(LOCAL_KHAN_PATH, path)
