# -*- coding: utf-8 -*-
"""
    localkhan.loader
    ~~~~~~~~~~~~~~~~
    Download Khan topic structure and media assets
    :copyright: (c) 2015 by Reto Aebersold.
    :license: MIT, see LICENSE for more details.
"""
import hashlib
import json
from contextlib import closing
import time

from clint.textui import progress

from localkhan import EX_OK

import re
import os
import requests
from requests.exceptions import InvalidSchema


MAX_CONNECTION_RETRIES = 5
MAX_DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 10  # seconds
KIND_VIDEO = 'Video'
TYPE_VIDEO = 'v'
TYPE_EXERCISE = 'e'
ASSET_FOLDER = 'assets'
MEDIA_URL_RE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:png|gif|jpeg|jpg|svg)')


class KhanLoaderError(Exception):
    pass


class KhanLoader(object):
    def __init__(self, base_path, base_url, language='en'):
        """
        Interacts with the Khan API to download the relevant topic structure and the corresponding media assets.

        :param base_path: directory to store the topic structure and media assets
        :param base_url: where the local Khan content is served
        :param language:
        :return:
        """
        self.api_url = 'http://{0}.khanacademy.org/api/v1/'.format(language)
        self.base_url = base_url
        self.base_path = base_path
        self.asset_url = base_url + '/' + ASSET_FOLDER
        self.asset_path = os.path.join(base_path, ASSET_FOLDER)

        # setup session and connection retries
        adapter = requests.adapters.HTTPAdapter(max_retries=MAX_CONNECTION_RETRIES)
        self.session = requests.Session()
        self.session.mount('http://', adapter)

        # create assets dir
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
    def get_base_data(topic, use_id=False):
        base_data = {
            'title': topic['translated_title']
        }
        if use_id:
            base_data['id'] = topic['id']
        else:
            base_data['slug'] = topic['node_slug']

        return base_data

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

        assets = set()

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
                tutorial_data['tutorial_contents'] = []

                tutorial_contents = self.get_topic(tutorial_data['slug'])

                for tutorial_content in tutorial_contents['children']:
                    tutorial_content_data = self.get_base_data(tutorial_content, use_id=True)

                    if tutorial_content['kind'] == KIND_VIDEO:
                        video_url = self.get_video(tutorial_content['id'])['download_urls']['mp4']
                        # extract video file name from url
                        video_store[tutorial_content['id']] = self.asset_url + '/' + video_url.split('/')[-1]
                        assets.add(video_url.replace('https://', 'http://'))
                        tutorial_content_data['type'] = TYPE_VIDEO
                    else:
                        exercise = self.get_exercise(tutorial_content['id'])

                        exercise_store[tutorial_content['id']] = []

                        for assessment_item in exercise['all_assessment_items']:
                            assessment = self.get_assessment_items(assessment_item['id'])

                            item_data = assessment["item_data"]
                            for media_url in set(MEDIA_URL_RE.findall(item_data)):
                                new_url = self.asset_url + '/' + media_url.split('/')[-1]
                                item_data = item_data.replace(media_url, new_url)
                                assets.add(media_url.replace('https://', 'http://'))

                            exercise_store[tutorial_content['id']].append(item_data)

                        tutorial_content_data['type'] = TYPE_EXERCISE

                    tutorial_data['tutorial_contents'].append(tutorial_content_data)

                topic_data['tutorials'].append(tutorial_data)

            topic_structure['topics'].append(topic_data)

        f = open(os.path.join(self.base_path, 'topics.json'), 'w')
        json.dump(topic_structure, f)
        f.close()

        f = open(os.path.join(self.base_path, 'videos.json'), 'w')
        json.dump(video_store, f)
        f.close()

        f = open(os.path.join(self.base_path, 'exercises.json'), 'w')
        json.dump(exercise_store, f)
        f.close()

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

    def _download_file(self, url):
        """
        Download given resource if not present in ASSET_FOLDER or md5sum in ETAG doesn't match.
        Retry to download MAX_DOWNLOAD_RETRIES times with a delay
        of DOWNLOAD_RETRY_DELAY seconds if status code is not 200.

        :param url:
        :return: file if any
        """
        local_filename = os.path.join(self.asset_path, url.split('/')[-1])

        # check if file already available and md5sum matches
        if os.path.isfile(local_filename):
            response = requests.head(url)
            if response.status_code == 200 and 'etag' in response.headers:
                md5 = self._generate_file_md5(local_filename)
                if response.headers['etag'].replace('"', '') == md5:
                    return

        retry = 0

        while retry < MAX_DOWNLOAD_RETRIES:
            with closing(self.session.get(url, stream=True)) as r:

                if r.status_code != 200:
                    print('Retry {0}'.format(url))
                    retry += 1
                    if retry == MAX_DOWNLOAD_RETRIES:
                        print('Unable to load resource at {0}: {1}'.format(url, r.content))
                        break
                    time.sleep(DOWNLOAD_RETRY_DELAY)
                    continue
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter keep-alive new chunks
                            f.write(chunk)
                            f.flush()
                    return

    def load(self, path):
        print('Downloading topics...')
        assets = self._load_structure(path)

        print('Downloading media assets...')
        for media_file in progress.bar(assets):
            try:
                self._download_file(media_file)
            except InvalidSchema as ins:
                print "InvalidSchema error({0}): {1}".format(ins.errno, ins.strerror)

        self.session.close()

        return EX_OK


def test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    loader = KhanLoader(os.path.join(base_dir, 'static/khan'), '/static/khan', language='es')
    loader.load('early-math/cc-early-math-counting-topic')


if __name__ == "__main__":
    test()
