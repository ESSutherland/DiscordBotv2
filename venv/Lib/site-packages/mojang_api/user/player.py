#!/usr/bin/env python3
from ..servers.api import (get_uuid, get_username_history, change_skin, upload_skin, reset_skin)
from ..servers.authserver import (authenticate_user, invalidate_access_token,
                                 refresh_access_token, signout_user,
                                 validate_access_token)
from ..servers.sessionserver import get_user_profile

class Player:
    def __init__(self, username='', uuid=''):
        self._validate(username, uuid)
        self._username = username
        self._uuid = uuid
        self._access_token=None
        self._client_token=None
        self._get_player()

    def _validate(self, username=None, uuid=None):
        if username is None:
            username = self.username

        if uuid is None:
            uuid = self.uuid

        if not (username or uuid):
            raise AttributeError('Player must contain a username or UUID')

    def _get_player(self):
        if not self.uuid and self.username:
            self.uuid = get_uuid(self)['data']['id']
        if not self.username and self.uuid:
            self.username = get_user_profile(self)['data']['name']

    def authenticate(self, username, password):
        resp=authenticate_user(username, password)
        if resp['response'].status_code == 200:
            data=resp['data']
            current_profile=data['selectedProfile']
            if current_profile:
                self._username=current_profile['name']
                self._uuid=current_profile['id']
                self._access_token=data['accessToken']
                self._client_token=data['clientToken']
                return True, resp
        return False, resp

    def signout(self):
        if self.is_authenticated:
            return invalidate_access_token(self._access_token, self._client_token)['response'].status_code == 204
        return False

    @property
    def is_authenticated(self):
        if self._access_token != None and self._client_token != None:
            return self.valid_tokens()
        return False

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        if username:
            self._username = username
        else:
            del self.username

    @username.deleter
    def username(self):
        self._validate(username='')
        self._username = ''

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        if uuid:
            self._uuid = uuid
        else:
            del self.uuid

    @uuid.deleter
    def uuid(self):
        self._validate(uuid='')
        self._uuid = ''

    @property
    def access_token(self):
        return self._access_token

    @property
    def tokens(self):
        return (self._access_token, self.clientToken)

    @tokens.setter
    def tokens(self, tokens):
        if tokens and len(tokens)==2 and tokens[0] and tokens[1]:
            if self._valid_tokens(tokens[0], tokens[1]):
                return self._refresh_tokens(tokens[0], tokens[1])
        else:
            del self.access_token
            del self.client_token
        return None

    def valid_tokens(self):
        return self._valid_tokens(self._access_token, self._client_token)

    def _valid_tokens(self, accessToken, clientToken):
        return validate_access_token(accessToken, clientToken)['response'].status_code==204

    def refresh_tokens(self):
        return self._refresh_tokens(self._access_token, self._client_token)

    def _refresh_tokens(self, access_token, client_token):
        resp = refresh_access_token(access_token, client_token, request_user=True)
        if resp['response'].status_code == 200:
            data=resp['data']
            self._access_token = data['accessToken']
            self._client_token = data['clientToken']
            self._username = data['selectedProfile']['name']
            self._uuid = data['selectedProfile']['id']
            return resp
        return None

    @access_token.deleter
    def access_token(self):
        if self._access_token and self._client_token:
            invalidate_access_token(self._access_token, self._client_token)
        self._access_token=None
        self._client_token=None

    @property
    def client_token(self):
        return self._client_token

    @client_token.deleter
    def client_token(self):
        if self._access_token and self._client_token:
            invalidate_access_token(self._access_token, self._client_token)
        self._access_token=None
        self._client_token=None

    @property
    def profile(self):
        return get_user_profile(self)

    def username_history(self):
        return get_username_history(self)

    def change_skin(self, skin_url, slim_model=False):
        assert self.is_authenticated, "Player must be authenticated to perform this action"
        return change_skin(player=self, access_token=self._access_token, skin_url=skin_url, slim_model=slim_model)

    def upload_skin(self, path_to_skin, slim_model=False):
        assert self.is_authenticated, "Player must be authenticated to perform this action"
        return upload_skin(player=self, access_token=self._access_token, path_to_skin=path_to_skin, slim_model=slim_model)

    def reset_skin(self):
        assert self.is_authenticated, "Player must be authenticated to perform this action"
        return reset_skin(player=self, access_token=self._access_token)
