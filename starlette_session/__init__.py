import json
from base64 import b64decode, b64encode
from typing import Any, Optional
from uuid import uuid4

import itsdangerous
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starlette_session.backends import (AioMemcacheSessionBackend,
                                        AioRedisSessionBackend, BackendType,
                                        MemcacheSessionBackend,
                                        RedisSessionBackend)
from starlette_session.interfaces import ISessionBackend


class UnknownPredefinedBackend(Exception):
    pass


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        cookie_name: str,
        max_age: int = 14 * 24 * 60 * 60,  # 14 days, in seconds
        same_site: str = "lax",
        https_only: bool = False,
        domain: Optional[str] = None,
        backend_type: Optional[BackendType] = None,
        backend_client: Optional[Any] = None,
        custom_session_backend: Optional[ISessionBackend] = None,
    ) -> None:
        """ Session Middleware

            Args:
                app: The ASGIApp
                secret_key: The secret key to use.
                cookie_name: The name of the cookie used to store the session id.
                max_age: The Max-Age of the cookie (Default to 14 days).
                same_site: The SameSite attribute of the cookie (Defaults to lax).
                https_only: Whether to make the cookie https only (Defaults to False).
                domain: The domain associated to the cookie (Default to None).
                backend_type: The type of predefined backend to use (Default to None,
                    if None we'll use a regular cookie backend).
                backend_client: The client to use in the predefined backend. See examples for examples
                    with predefined backends (Default to None).
                custom_session_backend: A custom backend that implement ISessionBackend.

            Raises:
                UnknownPredefinedBackend: The predefined backend type is unkown.
        """
        self.app = app

        self.backend_type = backend_type or BackendType.cookie
        self.session_backend = (
            custom_session_backend
            if custom_session_backend
            else self._get_predefined_session_backend(backend_client)
        )
        self.signer = itsdangerous.TimestampSigner(str(secret_key))
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.domain = domain

        self._cookie_session_id_field = "_cssid"

        self.security_flags = f"httponly; samesite={same_site}"
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        initial_session_was_empty = True

        if self.cookie_name in connection.cookies:
            data = connection.cookies[self.cookie_name].encode("utf-8")
            try:
                data = self.signer.unsign(data, max_age=self.max_age)
                if self.backend_type == BackendType.cookie or not self.session_backend:
                    scope["session"] = json.loads(b64decode(data))
                else:
                    session_key = json.loads(b64decode(data)).get(
                        self._cookie_session_id_field
                    )
                    scope["session"] = await self.session_backend.get(session_key)
                    scope["__session_key"] = session_key

                initial_session_was_empty = False
            except (BadTimeSignature, SignatureExpired):
                scope["session"] = {}
        else:
            scope["session"] = {}

        async def send_wrapper(message: Message, **kwargs) -> None:
            if message["type"] == "http.response.start":

                session_key = scope.pop("__session_key", str(uuid4()))

                if scope["session"]:

                    if (
                        self.backend_type == BackendType.cookie
                        or not self.session_backend
                    ):
                        cookie_data = scope["session"]
                    else:
                        await self.session_backend.set(
                            session_key, scope["session"], self.max_age
                        )
                        cookie_data = {self._cookie_session_id_field: session_key}

                    data = b64encode(json.dumps(cookie_data).encode("utf-8"))
                    data = self.signer.sign(data)

                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(clear=False, data=data)
                    headers.append("Set-Cookie", header_value)

                elif not initial_session_was_empty:

                    if self.session_backend and self.backend_type != BackendType.cookie:
                        await self.session_backend.delete(session_key)

                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(clear=True)
                    headers.append("Set-Cookie", header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _get_predefined_session_backend(
        self, backend_db_client
    ) -> Optional[ISessionBackend]:
        if self.backend_type == BackendType.redis:
            return RedisSessionBackend(backend_db_client)
        elif self.backend_type == BackendType.cookie:
            return None
        elif self.backend_type == BackendType.aioRedis:
            return AioRedisSessionBackend(backend_db_client)
        elif self.backend_type == BackendType.memcache:
            return MemcacheSessionBackend(backend_db_client)
        elif self.backend_type == BackendType.aioMemcache:
            return AioMemcacheSessionBackend(backend_db_client)
        else:
            raise UnknownPredefinedBackend()

    def _construct_cookie(self, clear: bool = False, data=None) -> str:
        if clear:
            cookie = f"{self.cookie_name}=null; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; {self.security_flags}"
        else:
            cookie = f"{self.cookie_name}={data.decode('utf-8')}; Path=/; Max-Age={self.max_age}; {self.security_flags}"
        if self.domain:
            cookie = f"{cookie}; Domain={self.domain}"
        return cookie
