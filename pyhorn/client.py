# Copyright (c) 2019 FLOW Executive Finders
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import logging
from datetime import datetime
from typing import AnyStr
from urllib import parse

import requests

import pyhorn.auth

__all__ = ['RESTClient', 'set_logger_level']

_logger = logging.getLogger("pyhorn")
_logger.setLevel(logging.CRITICAL)
_log_file_handler = logging.FileHandler(
    f"pyhorn_{datetime.now().timestamp()}.log")
_log_file_handler.setLevel(logging.DEBUG)
_log_file_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_log_file_handler.setFormatter(_log_file_format)

_logger.addHandler(_log_file_handler)

MAX_RECORDS = 200

_immutable_entities = [
    "BusinessSector", "Category", "Country", "ClientCorporation", "Skill",
    "Specialty", "State", "TimeUnit"
]


def set_logger_level(level: AnyStr):
    _logger.setLevel(level)


class RESTClient():
    def __init__(self, auth: pyhorn.auth.Credentials):
        self.auth = auth        

    def __compose_url(self, *args):
        return "/".join(args)

    def safe_request(self, method, url, **kwargs):
        try:
            _logger.debug(
                json.dumps({
                    "endpoint": f"{method} {url}",
                    "request": kwargs
                }))
            kwargs["headers"] = {
                **{
                    "BhRestToken": self.auth.BhRestToken
                },
                **(kwargs.get("headers") or {})
            }
            response = requests.request(method, url, **kwargs)
            _logger.debug(response.text)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self.auth.renew()
                self.safe_request(method, url, **kwargs)
            else:
                print(response.text)
                _logger.error(response.text)
                raise

    def authenticate(self):
        expiration = self.ping()
        if not expiration:
            self.auth.renew()

    def ping(self) -> datetime:
        """ Returns a datetime object with the current token's expiration,
            or None if the token is already expired.
        """
        try:
            full_url = self.__compose_url(self.auth.restUrl, "ping")
            headers = {"BhRestToken": self.auth.BhRestToken}
            response = requests.get(full_url, headers=headers)
            if response.status_code == 401:
                return None
            else:
                response.raise_for_status()
            data = response.json()
            return datetime.fromtimestamp(
                float(data["sessionExpires"]) / 1000.0)
        except KeyError as e:
            if e.args[0] == "restUrl":
                return None
            else:
                raise

    def get_entity(self, entity, entity_ids, **kwargs):
        params = {a: v for a, v in kwargs.items()}

        if type(entity_ids) is int:
            entity_ids = str(entity_ids)
        elif type(entity_ids) is list and type(entity_ids[0]) is int:
            entity_ids = ','.join([str(i) for i in entity_ids])
        else:
            raise TypeError("entityIds should be of type int or list(int)")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      entity_ids)
        full_url = f"{base_url}?{parse.urlencode(params)}"
        response = self.safe_request("GET", full_url)
        return response.json()

    def get_tomany(self, entity, entity_ids, tomany, **kwargs):
        params = {a: v for a, v in kwargs.items()}

        if type(entity_ids) is int:
            entity_ids = str(entity_ids)
        elif type(entity_ids) is list and type(entity_ids[0]) is int:
            entity_ids = ','.join([str(i) for i in entity_ids])
        else:
            raise TypeError("entityIds should be of type int or list(int)")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      entity_ids, tomany)
        full_url = f"{base_url}?{parse.urlencode(params)}"
        response = self.safe_request("GET", full_url)
        return response.json()

    def create_entity(self, entity, data):
        base_url = self.__compose_url(self.auth.restUrl, "entity", entity)
        response = self.safe_request("PUT", base_url, json=data)
        return response.json()

    def create_tomany(self, entity, entity_id, tomany, tomany_ids):
        if type(tomany_ids) is int:
            tomany_ids = str(tomany_ids)
        elif type(tomany_ids) is list and type(tomany_ids[0]) is int:
            tomany_ids = ','.join([str(i) for i in tomany_ids])
        else:
            raise TypeError("entityIds should be of type int or list(int)")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      str(entity_id), tomany, tomany_ids)
        response = self.safe_request("PUT", base_url)
        return response.json()

    def update_entity(self, entity, data):
        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      str(data["id"]))

        response = self.safe_request("POST", base_url, json=data)

        return response.json()

    def delete_entity(self, entity, entity_id):
        if entity in _immutable_entities:
            raise ValueError(
                "The DELETE operation does not support this entity type.")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      entity_id)
        response = self.safe_request("DELETE", base_url)
        return response.json()

    def delete_tomany(self, entity, entity_id, tomany, tomany_ids):
        if type(tomany_ids) is int:
            tomany_ids = str(tomany_ids)
        elif type(tomany_ids) is list and type(tomany_ids[0]) is int:
            tomany_ids = ','.join([str(i) for i in tomany_ids])
        else:
            raise TypeError("entityIds should be of type int or list(int)")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      entity_id, tomany, tomany_ids)
        response = self.safe_request("DELETE", base_url)
        return response.json()

    def query(self, entity, where, *args, **kwargs):
        params = {"where": where, **{a: v for a, v in kwargs.items()}}
        base_url = self.__compose_url(self.auth.restUrl, "query", entity)
        
        if len(where) >= 7500:
            response = self.safe_request("POST", base_url, json=params)
        else:
            full_url = f"{base_url}?{parse.urlencode(params)}"
            response = self.safe_request("GET", full_url)

        return response.json()

    def search(self, entity, query, *args, **kwargs):
        params = {"query": query, **{a: v for a, v in kwargs.items()}}

        base_url = self.__compose_url(self.auth.restUrl, "search", entity)
        if len(query) >= 7500:
            response = self.safe_request("POST", base_url, json=params)
        else:
            full_url = f"{base_url}?{parse.urlencode(params)}"
            response = self.safe_request("GET", full_url)

        return response.json()

    def capture(self, sub_id, max_events=100, **kwargs):
        params = {"maxEvents": max_events, **{k: v for k, v in kwargs.items()}}

        base_url = self.__compose_url(self.auth.restUrl, "event",
                                      "subscription", sub_id)
        full_url = f"{base_url}?{parse.urlencode(params)}"
        response = self.safe_request("GET", full_url)
        if int(response.headers["Content-Length"]) > 0:
            return response.json()
        else:
            return None

    def recapture(self, sub_id: AnyStr, request_id: int):
        return self.capture(sub_id, requestId=request_id)

    def get_last_capture_id(self, sub_id: AnyStr) -> int:
        base_url = self.__compose_url(self.auth.restUrl, "event",
                                      "subscription", sub_id, "lastRequestId")
        response = self.safe_request("GET", base_url)
        return response.json()['result']

    def subscribe(self, sub_id):        

        full_url = self.__compose_url(self.auth.restUrl, "event",
                                      "subscription", sub_id)

        response = self.safe_request("DELETE", full_url)
        return response.json()
        
    def delete_subscribe(self, sub_id: AnyStr):        

        base_url = self.__compose_url(self.auth.restUrl, "event",
                                      "subscription", sub_id)
        
        response = self.safe_request("DELETE", base_url)
        return response.json()

    def entity_file_attachment(self, entity, entity_ids, *args, **kwargs):
        params = {a: v for a, v in kwargs.items()}        

        if type(entity_ids) is int:
            entity_ids = str(entity_ids)
        elif type(entity_ids) is list and type(entity_ids[0]) is int:
            entity_ids = ','.join([str(i) for i in entity_ids])
        else:
            raise TypeError("entityIds should be of type int or list(int)")

        base_url = self.__compose_url(self.auth.restUrl, "entity", entity,
                                      entity_ids, "fileAttachments")
        full_url = f"{base_url}?{parse.urlencode(params)}"
        
        response = self.safe_request("GET", full_url)
        
        return response.json()

    def entity_edit_history(self, entity, where, *args, **kwargs):
        params = {"where": where, **{a: v for a, v in kwargs.items()}}       
        
        base_url = self.__compose_url(self.auth.restUrl, "query", f'{entity}EditHistory',)
        full_url = f"{base_url}?{parse.urlencode(params)}"
        
        response = self.safe_request("GET", full_url)                
        
        return response.json()
    
    def entity_edit_history_field_change(self, entity, where, *args, **kwargs):
        params = {"where": where, **{a: v for a, v in kwargs.items()}}       
        
        base_url = self.__compose_url(self.auth.restUrl, "query", f'{entity}EditHistoryFieldChange',)
        full_url = f"{base_url}?{parse.urlencode(params)}"
        
        response = self.safe_request("GET", full_url)                
        
        return response.json()

    def __enter__(self):
        _logger.debug("Starting REST Client...")
        self.authenticate()
        _logger.debug("Authenticated!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _logger.debug("Closed REST Client.")
        _logger.info(f"Exiting with: {exc_type}, {exc_val}, {exc_tb}")
