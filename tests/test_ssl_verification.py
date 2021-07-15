"""Tests to ensure that Api() works with unverified remote servers."""

import re
import ssl

import pytest
import trustme

from archfx_cloud.api.connection import Api
from archfx_cloud.api.exceptions import HttpCouldNotVerifyServerError


@pytest.fixture(scope="session")
def ca():
    return trustme.CA()


@pytest.fixture(scope="session")
def localhost_cert(ca):
    return ca.issue_cert("localhost")


@pytest.fixture(scope="session")
def httpserver_ssl_context(localhost_cert):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    crt = localhost_cert.cert_chain_pems[0]
    key = localhost_cert.private_key_pem
    with crt.tempfile() as crt_file, key.tempfile() as key_file:
        context.load_cert_chain(crt_file, key_file)

    return context


def test_deny_unverified_by_default(httpserver):
    """Ensure that we throw an error by default for self-signed servers."""
    httpserver.expect_request(re.compile(".+")).respond_with_data(status=204)

    api = Api(domain=httpserver.url_for("/"))

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.login('test@test.com', 'test')

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.logout()

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.refresh_token()

    # Also ensure that the RestResource works as well
    resource = api.event

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.get()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.put()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.patch()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.post()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.delete()


def test_allow_unverified_option(httpserver):
    """Ensure that we allow unverified servers if the user passes a flag."""
    # Any other status will cause some error. 204 silently skips all processing, it seems.
    httpserver.expect_request(re.compile(".+")).respond_with_data(status=204)

    api = Api(domain=httpserver.url_for("/"), verify=False)

    api.login('test@test.com', 'test')
    api.logout()
    api.refresh_token()

    # Also ensure that the RestResource works as well
    resource = api.event

    resource.get()
    resource.put()
    resource.patch()
    resource.post()
    resource.delete()
