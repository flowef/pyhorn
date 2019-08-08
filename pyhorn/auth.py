# Copyright (c) 2019 FLOW Executive Finders

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
from urllib import parse

import requests

LOGIN_URL = "https://rest.bullhornstaffing.com/rest-services/login"
TOKEN_URL = "https://auth.bullhornstaffing.com/oauth/token"
AUTHCODE_URL = "https://auth.bullhornstaffing.com/oauth/authorize"


class Credentials:
    def __init__(self, file_name):
        self.file_name = file_name

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value

    def __getattr__(self, attr):
        return self.__dict__[attr]

    @classmethod
    def from_json(cls, json_file: str):
        instance = cls(json_file)
        with open(json_file) as stream:
            for k, v in json.load(stream).items():
                setattr(instance, k, v)
        return instance

    def save(self):
        with open(self.file_name, 'w') as stream:
            json.dump(self.__dict__, stream, indent=True)

    def get_authorization_code(self):
        params = {"client_id": self.client_id, "response_type": "code"}
        login_data = {
            "username": self.username,
            "password": self.password,
            "action": "Login"
        }
        endpoint = f"{AUTHCODE_URL}?{parse.urlencode(params)}"
        response = requests.post(endpoint, login_data)

        query_string = parse.parse_qs(parse.urlparse(response.url).query)

        return query_string["code"][0]

    def get_access_token(self):
        request_params = {
            "grant_type": "authorization_code",
            "code": self.get_authorization_code(),
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        endpoint = f"{TOKEN_URL}?{parse.urlencode(request_params)}"
        new_auth = requests.post(endpoint)
        new_auth.raise_for_status()
        new_auth = new_auth.json()

        (self.access_token, self.refresh_token) = (new_auth["access_token"],
                                                   new_auth["refresh_token"])

    def renew_token(self):
        renewal_params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        endpoint = f"{TOKEN_URL}?{parse.urlencode(renewal_params)}"
        new_auth = requests.post(endpoint)
        new_auth.raise_for_status()
        new_auth = new_auth.json()

        (self.access_token, self.refresh_token) = (new_auth["access_token"],
                                                   new_auth["refresh_token"])

    def login(self) -> dict:
        query = {"access_token": self.access_token, "version": "*"}
        login = requests.post(f"{LOGIN_URL}?{parse.urlencode(query)}")
        login.raise_for_status()
        params = login.json()

        (self.restUrl, self.BhRestToken) = (params["restUrl"],
                                            params["BhRestToken"])

    def renew(self):
        try:
            self.renew_token()
        except requests.HTTPError as err:
            if err.response.status_code not in [400, 401]:
                raise
            self.get_access_token()
        self.login()
        self.save()

    def get_headers(self):
        return {"BhRestToken": self.BhRestToken}
