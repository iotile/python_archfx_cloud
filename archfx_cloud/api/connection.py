"""
See https://gist.github.com/dkarchmer/d85e55f9ed5450ba58cb
This API generically supports DjangoRestFramework based APIs
It is based on https://github.com/samgiles/slumber, but customized for
Django Rest Frameworks, and the use of TokenAuthentication.
Usage:
    # Assuming
    # v1_api_router.register(r'some_model', SomeModelViewSet)
    api = Api('http://127.0.0.1:8000')
    api.login(email='user1@test.com', password='user1')
    obj_list = api.some_model.get()
    logger.debug('Found {0} groups'.format(obj_list['count']))
    obj_one = api.some_model(1).get()
    api.logout()
"""
import logging
import requests
from archfx_cloud.api.exceptions import (
    ImproperlyConfigured,
    HttpClientError,
    HttpCouldNotVerifyServerError,
    HttpNotFoundError,
    HttpServerError,
    RestBaseException,
)

DOMAIN_NAME = 'https://arch.archfx.io'
API_PREFIX = 'api/v1'
DEFAULT_TOKEN_TYPE = 'jwt'

logger = logging.getLogger(__name__)


class RestResource:
    """
    Resource provides the main functionality behind a Django Rest Framework based API. It handles the
    attribute -> url, kwarg -> query param, and other related behind the scenes
    python to HTTP transformations. It's goal is to represent a single resource
    which may or may not have children.
    """

    def __init__(self, session, base_url, *args, **kwargs):
        self._session = session
        self._base_url = base_url
        self._store = kwargs

    def __call__(self, id=None):
        """
        Returns a new instance of self modified by one or more of the available
        parameters. These allows us to do things like override format for a
        specific request, and enables the api.resource(ID).get() syntax to get
        a specific resource by it's ID.
        """

        new_url = self._base_url

        if not new_url.endswith('/'):
            new_url += '/'

        if id:
            new_url += f'{id}/'

        return self._get_resource(session=self._session, base_url=new_url)

    def __getattr__(self, item):
        # Don't allow access to 'private' by convention attributes.
        if item.startswith("_"):
            raise AttributeError(item)

        kwargs = self._store.copy()
        return self._get_resource(self._session, f"{self._base_url}{item}/", **kwargs)

    def _get_resource(self, session, base_url, **kwargs):
        return self.__class__(session, base_url, **kwargs)

    def _check_for_errors(self, resp, url):
        if 400 <= resp.status_code <= 499:
            exception_class = HttpNotFoundError if resp.status_code == 404 else HttpClientError
            error_msg = 'Client Error {0}: {1}'.format(resp.status_code, url)
            if resp.status_code == 400 and resp.content:
                error_msg += ' ({0})'.format(resp.content)
            raise exception_class(error_msg, response=resp, content=resp.content)
        elif 500 <= resp.status_code <= 599:
            raise HttpServerError("Server Error %s: %s" % (resp.status_code, url), response=resp, content=resp.content)

    def _try_to_serialize_response(self, resp):
        if resp.status_code in [204, 205]:
            return

        if not resp.content:
            return resp.content
        try:
            return resp.json()
        except Exception:
            return resp.content

    def _process_response(self, resp):
        self._check_for_errors(resp, self._base_url)

        if 200 <= resp.status_code <= 299:
            return self._try_to_serialize_response(resp)
        else:
            return  # @@@ We should probably do some sort of error here? (Is this even possible?)

    def url(self):
        return self._base_url

    def _convert_ssl_exception(self, requester, **kwargs):
        try:
            return requester(self._base_url, **kwargs)
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err) from err

    def get(self, **kwargs):
        resp = self._convert_ssl_exception(self._session.get, params=kwargs)
        return self._process_response(resp)

    def post(self, data=None, **kwargs):
        resp = self._convert_ssl_exception(self._session.post, json=data, params=kwargs)
        return self._process_response(resp)

    def patch(self, data=None, **kwargs):
        resp = self._convert_ssl_exception(self._session.patch, json=data, params=kwargs)
        return self._process_response(resp)

    def put(self, data=None, **kwargs):
        resp = self._convert_ssl_exception(self._session.put, json=data, params=kwargs)
        return self._process_response(resp)

    def delete(self, data=None, **kwargs):
        resp = self._convert_ssl_exception(self._session.delete, json=data, params=kwargs)

        if 200 <= resp.status_code <= 299:
            if resp.status_code == 204:
                return True
            else:
                return True  # @@@ Should this really be True?
        else:
            return False

    def upload_fp(self, fp, data=None, **kwargs):
        """
        Upload a file from an opened file pointer

        Args:
            fp: File Pointer
            data: object with any additional payload data
            kwargs: additional parameters

        Returns:
            Object representing returned payload from server
        """
        files = {
            'file': fp
        }

        logger.debug('Uploading file to {}'.format(str(kwargs)))

        resp = self._convert_ssl_exception(self._session.post, data=data, files=files, params=kwargs)
        return self._process_response(resp)

    def upload_file(self, filename, data=None, mode='rb', **kwargs):
        """
        Upload a file from disk

        Args:
            filename: string representing valid file path
            data: object with any additional payload data
            mode: file mode
            kwargs: additional parameters

        Returns:
            Object representing returned payload from server
        """
        with open(filename, mode) as fp:
            return self.upload_fp(fp, data, **kwargs)

        raise RestBaseException("Unable to open and/or upload file")


class _TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
    """Custom http adapter to allow setting timeouts on http verbs.

    See https://github.com/psf/requests/issues/2011#issuecomment-64440818
    and surrounding discussion in that thread for why this is necessary.

    Short answer is that Session() objects don't support timeouts.
    """

    def __init__(self, timeout=None, *args, **kwargs):
        self.timeout = timeout
        super(_TimeoutHTTPAdapter, self).__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        kwargs['timeout'] = self.timeout
        return super(_TimeoutHTTPAdapter, self).send(*args, **kwargs)


class Api(object):
    token = None
    refresh_token_data = None
    token_type = DEFAULT_TOKEN_TYPE
    domain = DOMAIN_NAME
    resource_class = RestResource

    def __init__(self, domain=None, token_type=None, verify=True, timeout=None, retries=None):
        if domain:
            self.domain = domain

        self.base_url = f"{self.domain}/{API_PREFIX}"

        if token_type:
            self.token_type = token_type

        self.session = requests.Session()
        self.session.verify = verify

        if retries is not None or timeout is not None:
            adapter = _TimeoutHTTPAdapter(max_retries=retries, timeout=timeout)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)

    def _destroy_tokens(self):
        self.token = None
        self.refresh_token_data = None
        self.session.headers.pop("Authorization", "")

    def _validate_and_set_tokens(self, data):
        success = False
        if isinstance(data, str):
            self.token = data
            success = True
        elif "token" in data:
            self.token = data["token"]
            success = True
        elif "access" in data:
            self.token = data["access"]
            self.refresh_token_data = data["refresh"]
            success = True
        if success:
            self.session.headers["Authorization"] = f"{self.token_type} {self.token}"
        return success

    def set_token(self, token, token_type=None):
        if token_type:
            self.token_type = token_type
        if not self._validate_and_set_tokens(token):
            raise ImproperlyConfigured(f"Invalid token: %s")

    def url(self, section):
        return f"{self.base_url}/{section}/"

    def login(self, password, email):
        try:
            r = self.session.post(self.url("auth/login"), json={"email": email, "password": password})
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err) from err

        if r.status_code == 200:
            content = r.json()
            if access_token := content.get('jwt'):
                if not self._validate_and_set_tokens(access_token):
                    logger.warning(f"Incompatible JWT token received from server: {access_token}")
                if refresh_token := content.get('jwt_refresh_token'):
                    self.refresh_token_data = refresh_token

            self.username = content['username']
            logger.debug('Welcome @{0}'.format(self.username))
            return True
        else:
            logger.error("Login failed: " + str(r.status_code) + " " + r.content.decode())
            return False

    def logout(self):
        try:
            r = self.session.post(self.url("auth/logout"), json={})
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err) from err

        if r.status_code == 204:
            logger.debug('Goodbye @{0}'.format(self.username))
            self.username = None
            self._destroy_tokens()
        else:
            logger.error('Logout failed: %s %s', r.status_code, r.content.decode())

    def refresh_token(self):
        """
        Refresh JWT token

        :return: True if token was refreshed. False otherwise
        """
        assert self.token_type == DEFAULT_TOKEN_TYPE
        if self.refresh_token_data:
            data = {"refresh": self.refresh_token_data}
        else:
            data = {"token": self.token}

        try:
            r = self.session.post(self.url("auth/api-jwt-refresh"), json=data)
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err) from err

        if r.status_code == 200:
            content = r.json()
            if self._validate_and_set_tokens(content):
                logger.info('Token refreshed')
                return True

        logger.error("Token refresh failed: %s %s", r.status_code, r.content.decode())
        self._destroy_tokens()
        return False

    def __call__(self, id):
        return self.resource_class(session=self.session, base_url=self.url(id))

    def __getattr__(self, item):
        """
        Instead of raising an attribute error, the undefined attribute will
        return a Resource Instance which can be used to make calls to the
        resource identified by the attribute.
        """

        # Don't allow access to 'private' by convention attributes.
        if item.startswith("_"):
            raise AttributeError(item)

        return self.resource_class(session=self.session, base_url=self.url(item))
