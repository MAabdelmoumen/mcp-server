from typing import Any, Dict, Type
from pydantic import BaseModel
import requests
import re
import os
from urllib.parse import urljoin
import json


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to bool.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


class HttpClient:
    class Error(RuntimeError):
        pass

    def __init__(
        self,
        api_url: str,
        auth_url: str,
        username: str,
        password: str,
        tenant_id: str = "admin",
    ):
        protocol = re.match(r"^(\w+)://", api_url)
        if not protocol:
            api_url = "https://" + api_url
        self.__api_url = api_url
        self.__auth_url = auth_url
        self.__username = username
        self.__password = password
        self.__tenant_id = tenant_id
        self.__token = None

    def authenticate(self) -> None:
        data = {
            "grant_type": "password",
            "client_id": self.__tenant_id,
            "username": self.__username,
            "password": self.__password,
        }
        keycloak_url = urljoin(
            self.__auth_url, f"/realms/{self.__tenant_id}/protocol/openid-connect/token"
        )
        token_response = requests.post(
            keycloak_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=bool(strtobool(os.environ.get("VERIFY_SSL", "True"))),
        )
        json_response = token_response.json()
        if "access_token" not in json_response:
            raise Exception(
                f"No access_token found. Response: {json.dumps(json_response)}"
            )
        self.__token = json_response["access_token"]

    def get(self, url: str, model: Type[BaseModel]):
        assert self.__token is not None, "Not authenticated"
        res = requests.get(
            self.__api_url + url, headers={"Authorization": f"Bearer {self.__token}"}
        )
        if res.status_code != 200:
            raise HttpClient.Error(f"Request failed: {res.text}")
        return model(**res.json())

    def post(self, url: str, model: Type[BaseModel], data: Dict[str, Any]):
        assert self.__token is not None, "Not authenticated"
        res = requests.post(
            self.__api_url + url,
            headers={"Authorization": f"Bearer {self.__token}"},
            json=data,
        )
        if res.status_code != 200:
            raise HttpClient.Error(f"Request failed: {res.text}")
        return model(**res.json())

    def get_token(self) -> str:
        """Get the authentication token"""
        assert self.__token is not None, "Not authenticated"
        return self.__token

    def get_api_url(self) -> str:
        """Get the API URL"""
        return self.__api_url
