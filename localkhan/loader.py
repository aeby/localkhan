# -*- coding: utf-8 -*-
"""
    localkhan.loader
    ~~~~~~~~~~~~~~~~
    Download Khan topic structure and media assets
    :copyright: (c) 2015 by Reto Aebersold.
    :license: MIT, see LICENSE for more details.
"""

import json

from clint.textui import progress

import re
import os
import requests
from requests.exceptions import InvalidSchema


KIND_VIDEO = 'Video'
ASSET_FOLDER = 'assets'
MEDIA_URL_RE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:png|gif|jpeg|jpg|svg)')


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

        # create assets dir
        if not os.path.exists(self.asset_path):
            os.makedirs(self.asset_path)

    def get_resource(self, path):
        url = self.api_url + path
        response = requests.get(url)
        if response.status_code != 200:
            raise KhanLoaderError('Unable to load resource: {0}'.format(response.text))
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

    def load_structure(self, path):
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
            topics = [self.get_topic(t['slug']) for t in main_topic['children']]

        for topic in progress.bar(topics):
            topic_data = self.get_base_data(topic)
            topic_data['tutorials'] = []

            # filter tutorials
            if len(path_structure) > 2:
                tutorials = [self.get_topic(path_structure[2])]
            else:
                tutorials = [self.get_topic(t['slug']) for t in topic['children']]

            for tutorial in tutorials:
                tutorial_data = self.get_base_data(tutorial)
                tutorial_data['tutorial_contents'] = []

                tutorial_contents = self.get_topic(tutorial_data['slug'])

                for tutorial_content in tutorial_contents['children']:
                    tutorial_content_data = self.get_base_data(tutorial_content)

                    if tutorial_content['kind'] == KIND_VIDEO:
                        video_url = self.get_video(tutorial_content['id'])['download_urls']['mp4']
                        # extract video file name from url
                        video_store[tutorial_content['id']] = self.base_url + '/' + video_url.split('/')[-1]
                        assets.add(video_url.replace('https://', 'http://'))
                    else:
                        exercise = self.get_exercise(tutorial_content['id'])

                        exercise_store[tutorial_content['id']] = []

                        for assessment_item in exercise['all_assessment_items']:
                            assessment = self.get_assessment_items(assessment_item['id'])

                            item_data = assessment["item_data"]
                            for media_url in set(MEDIA_URL_RE.findall(item_data)):
                                new_url = self.base_url + '/' + media_url.split('/')[-1]
                                item_data = item_data.replace(media_url, new_url)
                                assets.add(media_url.replace('https://', 'http://'))

                            exercise_store[tutorial_content['id']].append(item_data)

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

    def download_file(self, url):
        local_filename = os.path.join(self.asset_path, url.split('/')[-1])
        r = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return local_filename

    def load(self, path):
        print('Downloading topics...')
        assets = self.load_structure(path)

        print('Downloading media assets...')
        for media_file in progress.bar(assets):
            try:
                self.download_file(media_file)
            except InvalidSchema as ins:
                print "InvalidSchema error({0}): {1}".format(ins.errno, ins.strerror)


def test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    loader = KhanLoader(os.path.join(base_dir, 'static/khan'), '/static/khan', language='es')
    loader.load('early-math/cc-early-math-counting-topic/cc-early-math-counting')


if __name__ == "__main__":
    test()
