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

from loader import TYPE_EXERCISE, TYPE_VIDEO, VIDEO_FORMAT
from localkhan import CONFIG
import os
from flask import Flask, send_from_directory, request
from flask import render_template, make_response

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Disable client cache
CACHE_CONTROL = 'no-cache, max-age=0, must-revalidate'


def get_manifest():
    """
    Creates the cache manifest content based on the asset index.
    :return: manifest file content
    """

    assets = []

    content_structure = ['exercises.json', 'topics.json', 'videos.json']
    assets.extend([os.path.join(CONFIG['STATIC_CONTENT_DIR'], a) for a in content_structure])

    with open(os.path.join(CONFIG['BASE_DIR'], 'assets.json')) as assets_file:
        for asset in json.load(assets_file):
            if asset['type'] == TYPE_EXERCISE:
                assets.append(
                    os.path.join(CONFIG['STATIC_CONTENT_DIR'], CONFIG['ASSET_DIR'], asset['uri'].split('/')[-1]))
            elif asset['type'] == TYPE_VIDEO:
                assets.append(
                    os.path.join(CONFIG['STATIC_CONTENT_DIR'], CONFIG['ASSET_DIR'], asset['uri'] + '.' + VIDEO_FORMAT))

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
    response.headers['Cache-Control'] = CACHE_CONTROL
    return response


@app.route('/khan.appcache')
def manifest():
    response = make_response(get_manifest())
    response.headers['Content-Type'] = 'text/cache-manifest'
    response.headers['Cache-Control'] = CACHE_CONTROL
    return response


@app.route('/static/khan/<path:path>')
def khan_content(path):
    return send_from_directory(CONFIG['BASE_DIR'], path)


@app.route('/static/khan/exercises.json')
def exercises():
    exercises_file = os.path.join(CONFIG['BASE_DIR'], 'exercises.json')

    with open(exercises_file) as khan_exercises:
        ex = khan_exercises.read()

    ex = ex.replace('{{host}}', request.host)

    response = make_response(ex)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = CACHE_CONTROL
    return response
