import json
import logging
from datetime import datetime
from urllib import parse

import requests

logger = logging.getLogger("bullhorn_api")
logger.setLevel(logging.DEBUG)
log_file_handler = logging.FileHandler("bullhorn.log")
log_file_handler.setLevel(logging.DEBUG)
log_file_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file_handler.setFormatter(log_file_format)

logger.addHandler(log_file_handler)

MAX_RECORDS = 200
AUTH_URL = "https://rest.bullhornstaffing.com/rest-services/login"
TOKEN_URL = "https://auth.bullhornstaffing.com/oauth/token"

ImmutableEntities = [
    "BusinessSector", "Category", "Country", "ClientCorporation", "Skill",
    "Specialty", "State", "TimeUnit"
]


def to_query_string(params: dict) -> str:
    """ Returns the given dictionary as a string with the format
    `key1=value1&...&keyN=valueN`.
    For use with `HTTP GET` query strings."""
    return "?{}".format('&'.join([f"{k}={v}" for k, v in params.items()]))


class Auth:
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
        base_url = "https://auth.bullhornstaffing.com/oauth/authorize"
        params = {"client_id": self.client_id, "response_type": "code"}
        login_data = {
            "username": self.username,
            "password": self.password,
            "action": "Login"
        }
        response = requests.post(f"{base_url}{to_query_string(params)}",
                                 login_data)

        query_string = parse.parse_qs(parse.urlparse(response.url).query)

        return query_string["code"][0]

    def get_access_token(self):
        request_params = {
            "grant_type": "authorization_code",
            "code": self.get_authorization_code(),
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        new_auth = requests.post(
            f"{TOKEN_URL}{to_query_string(request_params)}")
        new_auth.raise_for_status()
        new_auth = new_auth.json()

        self.access_token = new_auth["access_token"]
        self.refresh_token = new_auth["refresh_token"]

    def renew_token(self):
        renewal_params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        new_auth = requests.post(
            f"{TOKEN_URL}{to_query_string(renewal_params)}")
        new_auth.raise_for_status()
        new_auth = new_auth.json()

        self.access_token = new_auth["access_token"]
        self.refresh_token = new_auth["refresh_token"]

    def login(self) -> dict:
        login_params = {"access_token": self.access_token, "version": "*"}
        login = requests.post(f"{AUTH_URL}{to_query_string(login_params)}")
        login.raise_for_status()

        params = login.json()
        self.restUrl = params["restUrl"]
        self.BhRestToken = params["BhRestToken"]

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
                **self.auth.get_headers(),
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
        expiration = self.ping()
        if not expiration:
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
        full_url = f"{base_url}{to_query_string(params)}"
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
        full_url = f"{base_url}{to_query_string(params)}"
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
            full_url = f"{base_url}{to_query_string(params)}"
            response = self.safe_request("GET", full_url)

        return response.json()

    def search(self, entity, query, *args, **kwargs):
        params = {"query": query, **{a: v for a, v in kwargs.items()}}

        base_url = self.__compose_url(self.auth.restUrl, "search", entity)
        if len(query) >= 7500:
            response = self.safe_request("POST", base_url, json=params)
        else:
            full_url = f"{base_url}{to_query_string(params)}"
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
