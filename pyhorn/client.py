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
import logging
from datetime import datetime
from urllib import parse

import requests

logger = logging.getLogger("pyhorn")
logger.setLevel(logging.DEBUG)
log_file_handler = logging.FileHandler("pyhorn.log")
log_file_handler.setLevel(logging.DEBUG)
log_file_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file_handler.setFormatter(log_file_format)

logger.addHandler(log_file_handler)

MAX_RECORDS = 200

ImmutableEntities = [
    "BusinessSector", "Category", "Country", "ClientCorporation", "Skill",
    "Specialty", "State", "TimeUnit"
]


class RESTClient():
    def __init__(self, auth):
        self.auth = auth

    def __compose_url(self, *args):
        return "/".join(args)

    def safe_request(self, method, url, **kwargs):
        try:
            logger.debug(
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
            logger.debug(response.text)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self.authenticate()
                self.safe_request(method, url, **kwargs)
            else:
                logger.error(response.text)
                raise

    def authenticate(self):
        # expiration = self.ping()
        # if not expiration:
        self.auth.renew()

    def ping(self) -> datetime:
        """ Returns a datetime object with the current token's expiration,
            or None if the token is already expired.
        """
        full_url = self.__compose_url(self.auth.restUrl, "ping")

        response = requests.get(full_url, headers=self.auth.get_headers())
        if response.status_code == 401:
            return None
        else:
            response.raise_for_status()
        data = response.json()
        return datetime.fromtimestamp(float(data["sessionExpires"]) / 1000.0)

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
        if entity in ImmutableEntities:
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

    def __enter__(self):
        logger.debug("Starting REST Client...")
        self.authenticate()
        logger.debug("Authenticated!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Closed REST Client.")
        logger.info(f"Exiting with: {exc_type}, {exc_val}, {exc_tb}")
