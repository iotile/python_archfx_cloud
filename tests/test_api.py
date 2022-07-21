from io import BytesIO
import json
import requests
import requests_mock
import unittest

from archfx_cloud.api.connection import Api
from archfx_cloud.api.exceptions import HttpClientError, HttpServerError, ImproperlyConfigured


class ApiTestCase(unittest.TestCase):

    def test_init(self):
        api = Api()
        self.assertEqual(api.domain, 'https://arch.archfx.io')
        self.assertEqual(api.base_url, 'https://arch.archfx.io/api/v1')
        self.assertTrue(api.use_token)
        self.assertEqual(api.token_type, 'jwt')

    def test_set_token(self):
        api = Api()
        self.assertEqual(api.token, None)

        api.set_token('big-token')
        self.assertEqual(api.token, 'big-token')

        api.set_token({
            'access': 'access-token',
            'refresh': 'refresh-token',
        })
        self.assertEqual(api.token, 'access-token')
        self.assertEqual(api.refresh_token_data, 'refresh-token')

        api.set_token({
            'token': 'another-token',
        })
        self.assertEqual(api.token, 'another-token')
        self.assertEqual(api.refresh_token_data, 'refresh-token')

        with self.assertRaises(ImproperlyConfigured):
            api.set_token({
                'other': 'dummy',
            })

    @requests_mock.Mocker()
    def test_timeout(self, m):
        m.get('http://archfx.test/api/v1/timeout/', exc=requests.exceptions.ConnectTimeout )
        api = Api(domain='http://archfx.test', timeout=0.01)
        with self.assertRaises(requests.exceptions.ConnectTimeout):
            api.timeout.get()

    @requests_mock.Mocker()
    def test_login(self, m):
        payload = {
            'jwt': 'big-token',
            'username': 'user1'
        }
        m.post('http://archfx.test/api/v1/auth/login/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)
        self.assertEqual(api.username, 'user1')
        self.assertEqual(api.token, 'big-token')
        self.assertIsNone(api.refresh_token_data)

    @requests_mock.Mocker()
    def test_logout(self, m):
        payload = {
            'jwt': 'big-token',
            'username': 'user1'
        }

        # login works only if there is no Authorization header in the request
        def match_request_headers(request):
            return 'Authorization' not in request.headers
        m.post('http://archfx.test/api/v1/auth/login/', additional_matcher=match_request_headers, text=json.dumps(payload))
        m.post('http://archfx.test/api/v1/auth/logout/', status_code=204)

        api = Api(domain='http://archfx.test')
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)

        api.logout()
        self.assertEqual(api.username, None)
        self.assertEqual(api.token, None)

        # can log in again
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)

    @requests_mock.Mocker()
    def test_token_refresh(self, m):
        payload = {
            'token': 'new-token'
        }
        m.post('http://archfx.test/api/v1/auth/api-jwt-refresh/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        api.set_token('old-token')
        self.assertEqual(api.token, 'old-token')
        api.refresh_token()
        self.assertEqual(api.token, 'new-token')

    @requests_mock.Mocker()
    def test_login_new_jwt(self, m):
        m.post(
            'http://archfx.test/api/v1/auth/login/',
            additional_matcher=lambda request: 'Authorization' not in request.headers,
            json={
                'username': 'user1',
                'jwt': 'access-token',
                'jwt_refresh_token': 'refresh-token',
            }
        )
        api = Api(domain='http://archfx.test')
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)
        self.assertEqual(api.username, 'user1')
        self.assertEqual(api.token, 'access-token')
        self.assertEqual(api.refresh_token_data, 'refresh-token')

    @requests_mock.Mocker()
    def test_new_jwt_refresh(self, m):
        m.post(
            'http://archfx.test/api/v1/auth/login/',
            additional_matcher=lambda request: 'Authorization' not in request.headers,
            json={
                'username': 'user1',
                'jwt': 'access-token',
                'jwt_refresh_token': 'refresh-token',
            }
        )
        api = Api(domain='http://archfx.test')
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)

        m.post(
            'http://archfx.test/api/v1/auth/api-jwt-refresh/',
            additional_matcher=lambda request: request.json()['refresh'] == 'refresh-token',
            json={
                'access': 'new-access-token',
                'refresh': 'new-refresh-token',
            }
        )
        ok = api.refresh_token()
        self.assertTrue(ok)
        self.assertEqual(api.token, 'new-access-token')
        self.assertEqual(api.refresh_token_data, 'new-refresh-token')

    @requests_mock.Mocker()
    def test_upload_fp_content_type(self, m):
        """Testing that file upload doesn't accidentally inherit application/json content type"""
        m.post(
            'http://archfx.test/api/v1/test/',
            additional_matcher=lambda r: 'json' not in r.headers.get('Content-Type'),
            json={"result": "ok"},
        )

        api = Api(domain='http://archfx.test')
        resp = api.test.upload_fp(BytesIO(b"test"))  # "No mock address" means content-type is broken!
        self.assertEqual(resp['result'], 'ok')

        request_body = m.request_history[0]._request.body
        self.assertIn(b'Content-Disposition: form-data; name="file"; filename=', request_body)

    @requests_mock.Mocker()
    def test_get_list(self, m):
        payload = {
            "result": ["a", "b", "c"]
        }
        m.get('http://archfx.test/api/v1/test/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        resp = api.test.get()
        self.assertEqual(resp['result'], ['a', 'b', 'c'])

    @requests_mock.Mocker()
    def test_get_detail(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://archfx.test/api/v1/test/my-detail/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').get()
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_get_detail_with_action(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://archfx.test/api/v1/test/my-detail/action/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').action.url()
        self.assertEqual(resp, 'http://archfx.test/api/v1/test/my-detail/action/')
        resp = api.test('my-detail').action.get()
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_get_detail_with_extra_args(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://archfx.test/api/v1/test/my-detail/', text=json.dumps(payload))

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').get(foo='bar')
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_binary_response_content(self, m):
        m.get('http://archfx.test/api/v1/test/my-detail/', content=b'{"a": "b"}')

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').get(foo='bar')
        self.assertEqual(resp, {'a': 'b'})

    @requests_mock.Mocker()
    def test_post(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.post('http://archfx.test/api/v1/test/', text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        resp = api.test.post(payload)
        self.assertEqual(resp['id'], 1)

    @requests_mock.Mocker()
    def test_post_with_extra_args(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.post('http://archfx.test/api/v1/test/', text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        resp = api.test.post(payload, foo='bar')
        self.assertEqual(resp['id'], 1)

    @requests_mock.Mocker()
    def test_patch(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.patch('http://archfx.test/api/v1/test/my-detail/', text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').patch(payload)
        self.assertEqual(resp['id'], 1)

    @requests_mock.Mocker()
    def test_put(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.put('http://archfx.test/api/v1/test/my-detail/', text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        resp = api.test('my-detail').put(payload)
        self.assertEqual(resp['id'], 1)

    @requests_mock.Mocker()
    def test_delete(self, m):
        result = {
            "id": 1
        }
        m.delete('http://archfx.test/api/v1/test/my-detail/', text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        deleted = api.test('my-detail').delete()
        self.assertTrue(deleted)

    @requests_mock.Mocker()
    def test_post_with_error(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.post('http://archfx.test/api/v1/test/', status_code=400, text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        with self.assertRaises(HttpClientError):
            api.test.post(payload)

        m.post('http://archfx.test/api/v1/test/', status_code=404, text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        with self.assertRaises(HttpClientError):
            api.test.post(payload)

        m.post('http://archfx.test/api/v1/test/', status_code=500, text=json.dumps(result))

        api = Api(domain='http://archfx.test')
        with self.assertRaises(HttpServerError):
            api.test.post(payload)
