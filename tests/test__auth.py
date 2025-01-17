# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

import google.auth.credentials
import google_auth_httplib2
import httplib2
import socket
from googleapiclient.http import build_http
import oauth2client.client
import unittest2 as unittest

from googleapiclient import _auth


class TestAuthWithGoogleAuth(unittest.TestCase):
    def setUp(self):
        _auth.HAS_GOOGLE_AUTH = True
        _auth.HAS_OAUTH2CLIENT = False

    def tearDown(self):
        _auth.HAS_GOOGLE_AUTH = True
        _auth.HAS_OAUTH2CLIENT = True

    def test_default_credentials(self):
        with mock.patch('google.auth.default', autospec=True) as default:
            default.return_value = (
                mock.sentinel.credentials, mock.sentinel.project)

            credentials = _auth.default_credentials()

            self.assertEqual(credentials, mock.sentinel.credentials)

    def test_with_scopes_non_scoped(self):
        credentials = mock.Mock(spec=google.auth.credentials.Credentials)

        returned = _auth.with_scopes(credentials, mock.sentinel.scopes)

        self.assertEqual(credentials, returned)

    def test_with_scopes_scoped(self):
        class CredentialsWithScopes(
                google.auth.credentials.Credentials,
                google.auth.credentials.Scoped):
            pass

        credentials = mock.Mock(spec=CredentialsWithScopes)
        credentials.requires_scopes = True

        returned = _auth.with_scopes(credentials, mock.sentinel.scopes)

        self.assertNotEqual(credentials, returned)
        self.assertEqual(returned, credentials.with_scopes.return_value)
        credentials.with_scopes.assert_called_once_with(mock.sentinel.scopes)

    def test_authorized_http(self):
        credentials = mock.Mock(spec=google.auth.credentials.Credentials)

        authorized_http = _auth.authorized_http(credentials)

        self.assertIsInstance(
            authorized_http,
            google_auth_httplib2.AuthorizedHttp)
        self.assertEqual(authorized_http.credentials, credentials)
        self.assertIsInstance(authorized_http.http, httplib2.Http)
        self.assertIsInstance(authorized_http.http.timeout, int)
        # Check if the Http object's timeout is set to the default value.
        self.assertEqual(authorized_http.http.timeout, 60)


class TestAuthWithOAuth2Client(unittest.TestCase):
    def setUp(self):
        _auth.HAS_GOOGLE_AUTH = False
        _auth.HAS_OAUTH2CLIENT = True

    def tearDown(self):
        _auth.HAS_GOOGLE_AUTH = True
        _auth.HAS_OAUTH2CLIENT = True

    def test_default_credentials(self):
        default_patch = mock.patch(
            'oauth2client.client.GoogleCredentials.get_application_default')

        with default_patch as default:
            default.return_value = mock.sentinel.credentials

            credentials = _auth.default_credentials()

            self.assertEqual(credentials, mock.sentinel.credentials)

    def test_with_scopes_non_scoped(self):
        credentials = mock.Mock(spec=oauth2client.client.Credentials)

        returned = _auth.with_scopes(credentials, mock.sentinel.scopes)

        self.assertEqual(credentials, returned)

    def test_with_scopes_scoped(self):
        credentials = mock.Mock(spec=oauth2client.client.GoogleCredentials)
        credentials.create_scoped_required.return_value = True

        returned = _auth.with_scopes(credentials, mock.sentinel.scopes)

        self.assertNotEqual(credentials, returned)
        self.assertEqual(returned, credentials.create_scoped.return_value)
        credentials.create_scoped.assert_called_once_with(mock.sentinel.scopes)

    def test_authorized_http(self):
        credentials = mock.Mock(spec=oauth2client.client.Credentials)
        
        # Overriding the default timeout value of the Http object.
        socket.setdefaulttimeout(42.0)
        http = build_http()
        
        authorized_http = _auth.authorized_http(credentials, http)

        http = credentials.authorize.call_args[0][0]

        self.assertEqual(authorized_http, credentials.authorize.return_value)
        self.assertIsInstance(http, httplib2.Http)
        self.assertIsInstance(http.timeout, float)
        # Check if the Http object's timeout is set to the override value.
        self.assertEqual(http.timeout, 42.0)


class TestAuthWithoutAuth(unittest.TestCase):

    def setUp(self):
        _auth.HAS_GOOGLE_AUTH = False
        _auth.HAS_OAUTH2CLIENT = False

    def tearDown(self):
        _auth.HAS_GOOGLE_AUTH = True
        _auth.HAS_OAUTH2CLIENT = True

    def test_default_credentials(self):
        with self.assertRaises(EnvironmentError):
            print(_auth.default_credentials())


class TestGoogleAuthWithoutHttplib2(unittest.TestCase):
    def setUp(self):
        _auth.google_auth_httplib2 = None

    def tearDown(self):
        _auth.google_auth_httplib2 = google_auth_httplib2

    def test_default_credentials(self):
        credentials = mock.Mock(spec=google.auth.credentials.Credentials)
        with self.assertRaises(ValueError):
            _auth.authorized_http(credentials)
