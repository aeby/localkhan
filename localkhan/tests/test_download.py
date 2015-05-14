import hashlib
import unittest

import httpretty

from localkhan.loader import KhanLoader, MAX_DOWNLOAD_RETRIES, ASSET_FOLDER
from mock import patch
import os
from testfixtures import TempDirectory


class DownloadTestCase(unittest.TestCase):
    @httpretty.activate
    def test_etag(self):
        data = b'img'
        etag = hashlib.md5(data).hexdigest()
        httpretty.register_uri(httpretty.HEAD, 'http://khan.com/test.png',
                               status=200,
                               etag=etag)
        with TempDirectory() as d:
            d.makedir(ASSET_FOLDER)
            d.write(os.path.join(ASSET_FOLDER, 'test.png'), data)
            loader = KhanLoader(d.path, '/static/khan')
            loader._download_file('http://khan.com/test.png')

        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @patch('time.sleep', return_value=None)
    @httpretty.activate
    def test_failed_download(self, sleep):
        httpretty.register_uri(httpretty.GET, 'http://khan.com/topic',
                               status=403)
        with TempDirectory() as d:
            loader = KhanLoader(d.path, '/static/khan')
            loader._download_file('http://khan.com/topic')

        self.assertEqual(len(httpretty.httpretty.latest_requests), MAX_DOWNLOAD_RETRIES)

    @patch('time.sleep', return_value=None)
    @httpretty.activate
    def test_failed_head(self, sleep):
        httpretty.register_uri(httpretty.HEAD, 'http://khan.com/test.png',
                               status=403)
        httpretty.register_uri(httpretty.GET, 'http://khan.com/test.png',
                               status=200)
        with TempDirectory() as d:
            d.makedir(ASSET_FOLDER)
            d.write(os.path.join(ASSET_FOLDER, 'test.png'), b'img')
            loader = KhanLoader(d.path, '/static/khan')
            loader._download_file('http://khan.com/test.png')

        # assert MAX_DOWNLOAD_RETRIES for head and 1 for file download request
        self.assertEqual(len(httpretty.httpretty.latest_requests), MAX_DOWNLOAD_RETRIES + 1)


if __name__ == '__main__':
    unittest.main()
