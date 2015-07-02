# -*- coding: utf-8 -*-
"""
    localkhan.loader
    ~~~~~~~~~~~~~~~~
    Download Khan topic structure and media assets
    :copyright: (c) 2015 by Reto Aebersold.
    :license: MIT, see LICENSE for more details.
"""
from __future__ import print_function
import hashlib
import json
from contextlib import closing
import time

from clint.textui import progress

from localkhan import EX_OK, CONFIG
from pytube import YouTube
import re
import os
import requests
from requests.exceptions import RequestException, InvalidSchema

MAX_CONNECTION_RETRIES = 5
MAX_DOWNLOAD_RETRIES = 10
DOWNLOAD_RETRY_DELAY = 30  # seconds
DOWNLOAD_TIMEOUT = 30  # seconds
KIND_VIDEO = 'Video'
KIND_EXERCISE = 'Exercise'
TYPE_VIDEO = 'v'
TYPE_EXERCISE = 'e'
VIDEO_FORMAT = 'mp4'

IMAGE_URL_RE = re.compile(
    'http[s]?://ka-perseus-(?:images|graphie)\.s3\.amazonaws.com/(?:[a-zA-Z]|[0-9])+\.(?:png|gif|jpeg|jpg|svg)')

GRAPHIE_URL_RE = re.compile(
    'web\+graphie://ka-perseus-graphie\.s3\.amazonaws\.com/(?:[a-zA-Z]|[0-9])+')


class KhanLoaderError(Exception):
    pass


class KhanLoader(object):
    def __init__(self, base_path, base_url, language='en', media_only=False):
        """
        Interacts with the Khan API to download the relevant topic structure and the corresponding media assets.

        :param base_path: directory to store the topic structure and media assets
        :param base_url: where the local Khan content is served
        :param language:
        :return:
        """
        self.api_url = 'http://{0}.khanacademy.org/api/v1/'.format(language)
        self.base_url = base_url
        if not self.base_url.startswith('/'):
            self.base_url = '/' + self.base_url
        self.base_path = base_path
        self.asset_url = base_url + '/' + CONFIG['ASSET_DIR']
        self.asset_path = os.path.join(base_path, CONFIG['ASSET_DIR'])
        self.media_only = media_only

        # setup session and connection retries
        adapter = requests.adapters.HTTPAdapter(max_retries=MAX_CONNECTION_RETRIES)
        self.session = requests.Session()
        self.session.mount('http://', adapter)

        self.yt = YouTube()

        # create asset dir
        if not os.path.exists(self.asset_path):
            os.makedirs(self.asset_path)

    def get_resource(self, path):
        url = self.api_url + path
        response = self.session.get(url)
        if response.status_code != 200:
            raise KhanLoaderError('Unable to load resource at {0}: {1}'.format(path, response.text))
        return json.loads(response.text)

    def get_topic(self, name):
        return self.get_resource('topic/' + name)

    def get_video(self, name):
        return self.get_resource('videos/' + name)

    def get_exercise(self, name):
        return self.get_resource('exercises/' + name)

    def get_assessment_items(self, name):
        return self.get_resource('assessment_items/' + name)

    @staticmethod
    def get_base_data(topic):
        return {
            'title': topic['translated_title'],
            'slug': topic['node_slug']
        }

    @staticmethod
    def path_segments(path):
        return [path for path in path.split('/') if len(path) > 0]

    def _load_structure(self, path):
        """
        Download topic structure. For a path with 2 or 3 segments the topics and tutorials are filtered by those
        segment names. Eg. "early-math/cc-early-math-counting-topic/cc-early-math-counting" will just load the
        "cc-early-math-counting-topic" topic and the "cc-early-math-counting" tutorial.

        The topic structure is saved to "topics.json", all exercise data to "exercises.json" and
        all videos to "videos.json".
        All media assets URLs are rewritten (and prefixed with self.asset_url) to be served from the local server.

        :param path: 1 - 3 level deep path of Khan tutorials
        :return: set of assets to download
        """
        path_structure = self.path_segments(path)

        topic_structure = {
            'topics': []
        }

        video_store = {}
        exercise_store = {}
        assets = []

        def add_asset(asset):
            # add asset only if name and type are unique
            if not any(a for a in assets if a['uri'] == asset['uri'] and a['type'] == asset['type']):
                assets.append(asset)

        main_topic = self.get_topic(path_structure[0])

        # filter topics
        if len(path_structure) > 1:
            topics = [self.get_topic(path_structure[1])]
        else:
            topics = [self.get_topic(t['node_slug']) for t in main_topic['children']]

        for topic in progress.bar(topics):
            topic_data = self.get_base_data(topic)
            topic_data['tutorials'] = []

            # filter tutorials
            if len(path_structure) > 2:
                tutorials = [self.get_topic(path_structure[2])]
            else:
                tutorials = [self.get_topic(t['node_slug']) for t in topic['children']]

            for tutorial in tutorials:
                tutorial_data = self.get_base_data(tutorial)
                tutorial_data['tutorialContents'] = []

                tutorial_contents = self.get_topic(tutorial_data['slug'])

                for tutorial_content in tutorial_contents['children']:
                    tutorial_content_data = self.get_base_data(tutorial_content)
                    tutorial_content_data['id'] = tutorial_content['id']

                    if tutorial_content['kind'] == KIND_VIDEO:
                        video_id = self.get_video(tutorial_content_data['id'])['translated_youtube_id']
                        video_store[tutorial_content_data['id']] = self.asset_url + '/' + video_id + '.mp4'
                        add_asset({
                            'type': TYPE_VIDEO,
                            'uri': video_id
                        })
                        tutorial_content_data['type'] = TYPE_VIDEO
                    elif tutorial_content['kind'] == KIND_EXERCISE:
                        exercise = self.get_exercise(tutorial_content_data['id'])

                        # filter legacy khan exercises
                        if len(exercise['all_assessment_items']) == 0:
                            continue

                        exercise_store[tutorial_content_data['id']] = []

                        for assessment_item in exercise['all_assessment_items']:
                            assessment = self.get_assessment_items(assessment_item['id'])

                            item_data = assessment['item_data']

                            for image_url in set(IMAGE_URL_RE.findall(item_data)):
                                local_img_url = self.asset_url + '/' + image_url.split('/')[-1]
                                item_data = item_data.replace(image_url, local_img_url)
                                add_asset({
                                    'type': TYPE_EXERCISE,
                                    'uri': image_url.replace('https://', 'http://')
                                })

                            for graphie_url in set(GRAPHIE_URL_RE.findall(item_data)):
                                graphie_id = graphie_url.split('/')[-1]
                                local_graphie_url = 'web+graphie://{{host}}/' + self.asset_url + '/' + graphie_id
                                item_data = item_data.replace(graphie_url, local_graphie_url)
                                add_asset({
                                    'type': TYPE_EXERCISE,
                                    'uri': 'http://ka-perseus-graphie.s3.amazonaws.com/' + graphie_id + '.svg'
                                })
                                add_asset({
                                    'type': TYPE_EXERCISE,
                                    'uri': 'http://ka-perseus-graphie.s3.amazonaws.com/' + graphie_id + '-data.json'
                                })

                            # Load item_data as json and set answer area options content to empty string.
                            # Not sure if this field is used anymore as it is mostly empty and
                            # only partially translated.
                            item_data_json = json.loads(item_data)
                            if 'content' in item_data_json['answerArea']['options']:
                                item_data_json['answerArea']['options']['content'] = ''
                            exercise_store[tutorial_content_data['id']].append(item_data_json)

                        tutorial_content_data['type'] = TYPE_EXERCISE

                    # only append if it was a video or exercise
                    if tutorial_content['kind'] in [KIND_EXERCISE, KIND_VIDEO]:
                        tutorial_data['tutorialContents'].append(tutorial_content_data)

                topic_data['tutorials'].append(tutorial_data)

            topic_structure['topics'].append(topic_data)

        with open(os.path.join(self.base_path, 'topics.json'), 'w') as topics_file:
            json.dump(topic_structure, topics_file)

        with open(os.path.join(self.base_path, 'videos.json'), 'w') as videos_file:
            json.dump(video_store, videos_file)

        with open(os.path.join(self.base_path, 'exercises.json'), 'w') as exercises_file:
            json.dump(exercise_store, exercises_file)

        return assets

    @staticmethod
    def _generate_file_md5(filename, block_size=2 ** 20):
        m = hashlib.md5()
        with open(filename, "rb") as f:
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                m.update(buf)
        return m.hexdigest()

    def _download_exercise_media(self, url):
        """
        Download given resource if not present in ASSET_DIR or md5sum in ETAG doesn't match.
        Retry to download MAX_DOWNLOAD_RETRIES times with a delay
        of DOWNLOAD_RETRY_DELAY seconds if status code is not 200.

        :param url:
        :return: file if any
        """
        local_filename = os.path.join(self.asset_path, url.split('/')[-1])

        # check if file already available and md5sum matches
        if os.path.isfile(local_filename):
            retry = 0
            while retry < MAX_DOWNLOAD_RETRIES:
                try:
                    response = requests.head(url)
                    if response.status_code == 200:
                        if 'etag' in response.headers:
                            md5 = self._generate_file_md5(local_filename)
                            # do nothing if md5 hash matches
                            if response.headers['etag'].replace('"', '') == md5:
                                return
                            else:
                                break
                    else:
                        raise RequestException(response=response)
                except IOError as ie:
                    print('Retry {0}: {1}'.format(url, ie))
                    retry += 1
                    time.sleep(DOWNLOAD_RETRY_DELAY)
                    continue

        retry = 0
        while retry < MAX_DOWNLOAD_RETRIES:
            try:
                with closing(self.session.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)) as r:
                    if r.status_code != 200:
                        raise RequestException(response=r)
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:  # filter keep-alive new chunks
                                f.write(chunk)
                                f.flush()
                        return
            except IOError as ie:
                print('Retry {0}: {1}'.format(url, ie))
                retry += 1
                time.sleep(DOWNLOAD_RETRY_DELAY)
                continue

        if retry == MAX_DOWNLOAD_RETRIES:
            print('Unable to load resource at {0}'.format(url))

    def load(self, path):
        assets_path = os.path.join(self.base_path, 'assets.json')

        if self.media_only:
            with open(assets_path) as assets_file:
                assets = json.load(assets_file)
        else:
            print('Downloading topics...')
            assets = self._load_structure(path)

            # save assets for later media download and cache manifest creation
            with open(assets_path, 'w') as assets_file:
                json.dump(assets, assets_file)

        print('Downloading assets ...')

        for asset in progress.bar(assets):
            if asset['type'] == TYPE_EXERCISE:
                try:
                    self._download_exercise_media(asset['uri'])
                except InvalidSchema as ins:
                    print('InvalidSchema error({0}): {1}'.format(ins.errno, ins.strerror))
            elif asset['type'] == TYPE_VIDEO:
                retry = 0
                while retry < MAX_DOWNLOAD_RETRIES:
                    try:
                        video = os.path.join(self.asset_path, asset['uri'] + '.' + VIDEO_FORMAT)
                        if not os.path.isfile(video):
                            self.yt.url = 'http://www.youtube.com/watch?v=' + asset['uri']
                            video = self.yt.get(extension=VIDEO_FORMAT, resolution='360p', profile='Baseline')
                            video.filename = asset['uri']
                            video.download(self.asset_path)
                        break
                    except IOError as ue:
                        print('Retry {0}: {1}'.format(self.yt.url, ue))
                        retry += 1
                        time.sleep(DOWNLOAD_RETRY_DELAY)
                        continue

                if retry == MAX_DOWNLOAD_RETRIES:
                    print('Unable to load resource at {0}: {1}'.format(self.yt.url, asset['uri']))

        self.session.close()
        return EX_OK


def test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    loader = KhanLoader(os.path.join(base_dir, 'static/khan'), '/static/khan', language='es')
    loader.load('arithmetic/fractions/Adding_and_subtracting_fractions')


if __name__ == '__main__':
    test()
