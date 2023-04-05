import json
import os.path
import unittest
from argparse import Namespace

import mock
import requests_mock

from archfx_cloud.utils.main import BaseMain


class MainTestCase(unittest.TestCase):
    @requests_mock.Mocker()
    @mock.patch('archfx_cloud.utils.main.argparse.ArgumentParser.parse_args')
    @mock.patch('archfx_cloud.utils.main.getpass.getpass')
    def test_main_login_email_password_ok(
        self, mock_request, mock_getpass, mock_parse_args
    ):
        mock_request.post(
            'https://test.archfx.io/api/v1/auth/login/',
            text=json.dumps({'jwt': 'big-token', 'username': 'user1'}),
        )
        mock_request.post(
            'https://test.archfx.io/api/v1/auth/logout/', status_code=204
        )
        mock_getpass.return_value = 'password'
        mock_parse_args.return_value = Namespace(
            customer='test', server_type='prod', email='user1@test.com'
        )

        main = BaseMain()
        main.main()

        self.assertEqual(len(mock_request.request_history), 2)
        self.assertEqual(
            mock_request.request_history[0].url,
            'https://test.archfx.io/api/v1/auth/login/',
        )
        self.assertTrue(
            'Authorization' not in mock_request.request_history[0].headers
        )
        self.assertEqual(
            json.loads(mock_request.request_history[0].body),
            {'email': 'user1@test.com', 'password': 'password'},
        )
        self.assertEqual(
            mock_request.request_history[1].url,
            'https://test.archfx.io/api/v1/auth/logout/',
        )
        self.assertEqual(
            mock_request.request_history[1].headers['Authorization'],
            'jwt big-token',
        )

    @requests_mock.Mocker()
    @mock.patch('archfx_cloud.utils.main.argparse.ArgumentParser.parse_args')
    def test_main_login_token_file_ok(self, mock_request, mock_parse_args):
        mock_request.get(
            'https://test.archfx.io/api/v1/auth/user-info/',
            text=json.dumps({'email': 'user1@test.com'}),
        )
        mock_request.post(
            'https://test.archfx.io/api/v1/auth/logout/', status_code=204
        )
        mock_parse_args.return_value = Namespace(
            customer='test',
            server_type='prod',
        )

        main = BaseMain(
            config_path=f'{os.path.dirname(__file__)}/data/test_main_login_token_file.ini'
        )
        main.main()

        self.assertEqual(len(mock_request.request_history), 2)
        self.assertEqual(
            mock_request.request_history[0].url,
            'https://test.archfx.io/api/v1/auth/user-info/',
        )
        self.assertEqual(
            mock_request.request_history[0].headers['Authorization'],
            'token test-token',
        )
        self.assertEqual(
            mock_request.request_history[1].url,
            'https://test.archfx.io/api/v1/auth/logout/',
        )
        self.assertEqual(
            mock_request.request_history[1].headers['Authorization'],
            'token test-token',
        )

    @mock.patch('archfx_cloud.utils.main.argparse.ArgumentParser.parse_args')
    def test_main_login_token_file_ko(self, mock_parse_args):
        mock_parse_args.return_value = Namespace(
            customer='test',
            server_type='prod',
            email=None,
        )

        main = BaseMain(config_path=f'non_existing_config_file.ini')

        with self.assertRaises(SystemExit) as e:
            main.main()

        self.assertEqual(e.exception.code, 1)
