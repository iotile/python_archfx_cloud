import json
import requests
import requests_mock
import unittest

from archfx_cloud.api.connection import RestResource


class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.base_resource = RestResource(
            session=requests.Session(),
            base_url="http://archfx.test/api/v1/test/",
        )

    def test_url(self):

        url = self.base_resource.url()
        self.assertEqual(url, 'http://archfx.test/api/v1/test/')

    @requests_mock.Mocker()
    def test_get_200(self, m):
        payload = {
            "result": ["a", "b", "c"]
        }
        m.get('http://archfx.test/api/v1/test/', text=json.dumps(payload))

        resp = self.base_resource.get()
        self.assertEqual(resp['result'], ['a', 'b', 'c'])

