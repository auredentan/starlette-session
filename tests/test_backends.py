import re

import fakeredis
import pytest

from pymemcache.test.utils import MockMemcacheClient

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType, MemcacheJSONSerde


def view_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": request.session})


async def update_session(request: Request) -> JSONResponse:
    data = await request.json()
    request.session.update(data)
    return JSONResponse({"session": request.session})


async def clear_session(request: Request) -> JSONResponse:
    request.session.clear()
    return JSONResponse({"session": request.session})


@pytest.fixture
def app():
    app = Starlette()
    app.add_route("/view_session", view_session)
    app.add_route("/update_session", update_session, methods=["POST"])
    app.add_route("/clear_session", clear_session, methods=["POST"])
    return app


@pytest.fixture
def redis() -> fakeredis.FakeStrictRedis:
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def memcache():
    return MockMemcacheClient()

def test_MemcacheJSONSerde():
    serde = MemcacheJSONSerde()

    assert serde.serialize("key", "test") == ("test", 1)

    assert serde.serialize("key", {"key1": "test"}) == ('{"key1": "test"}', 2)

    assert serde.deserialize("key", "value", 1) == "value"

    assert serde.deserialize("key", '{"key1": "test"}', 2) == {"key1": "test"}

    with pytest.raises(Exception):
        serde.deserialize("key", '{"key1": "test"}', -1)


def test_without_backend(app):

    app.add_middleware(SessionMiddleware, secret_key="secret", cookie_name="cookie")
    client = TestClient(app)

    response = client.get("/view_session")
    assert response.json() == {"session": {}}

    response = client.post("/update_session", json={"data": "something"})
    assert response.json() == {"session": {"data": "something"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    max_age_matches = re.search(r"; Max-Age=([0-9]+);", set_cookie)
    assert max_age_matches is not None
    assert int(max_age_matches[1]) == 14 * 24 * 3600

    response = client.post("/clear_session")
    assert response.json() == {"session": {}}


def test_with_redis_backend(mocker, app, redis):

    app.add_middleware(
        SessionMiddleware,
        secret_key="secret",
        cookie_name="cookie",
        backend_type=BackendType.redis,
        backend_client=redis,
    )
    client = TestClient(app)

    spy_redis_set = mocker.spy(redis, "set")
    spy_redis_get = mocker.spy(redis, "get")
    spy_redis_delete = mocker.spy(redis, "delete")

    response = client.get("/view_session")
    assert response.json() == {"session": {}}

    response = client.post("/update_session", json={"data": "something"})
    assert response.json() == {"session": {"data": "something"}}
    spy_redis_set.assert_called_once()

    response = client.get("/view_session")
    spy_redis_get.assert_called_once()

    response = client.post("/clear_session")
    assert response.json() == {"session": {}}
    spy_redis_delete.assert_called_once()


def test_with_memcache_backend(mocker, app, memcache):

    app.add_middleware(
        SessionMiddleware,
        secret_key="secret",
        cookie_name="cookie",
        backend_type=BackendType.memcache,
        backend_client=memcache,
    )
    client = TestClient(app)

    spy_redis_set = mocker.spy(memcache, "set")
    spy_redis_get = mocker.spy(memcache, "get")
    spy_redis_delete = mocker.spy(memcache, "delete")

    response = client.get("/view_session")
    assert response.json() == {"session": {}}

    response = client.post("/update_session", json={"data": "something"})
    assert response.json() == {"session": {"data": "something"}}
    spy_redis_set.assert_called_once()

    response = client.get("/view_session")
    spy_redis_get.assert_called_once()

    response = client.post("/clear_session")
    assert response.json() == {"session": {}}
    spy_redis_delete.assert_called_once()
