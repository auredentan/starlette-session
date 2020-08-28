<p align="center">

<a href="https://github.com/auredentan/starlette-session/actions?query=workflow%3ATest" target="_blank">
  <img src="https://github.com/auredentan/starlette-session/workflows/Test/badge.svg?branch=master" alt="Test"/>
</a>

<a href="https://pypi.org/project/starlette-session" target="_blank">
  <img src="https://img.shields.io/pypi/v/starlette-session?color=%2334D058&label=pypi%20package" alt="Package version"/>
</a>

<a href="https://codecov.io/gh/auredentan/starlette-session" target="_blank">
  <img src="https://codecov.io/gh/auredentan/starlette-session/branch/master/graph/badge.svg" alt="Code coverage"/>
</a>

</p>

---

**Documentation:** [https://auredentan.github.io/starlette-session/](https://auredentan.github.io/starlette-session/)

---

# Starlette Session

Starlette session is a simple session middleware for [starlette](https://github.com/encode/starlette/) that enable backend side session with starlette.

## Requirements

Python 3.6+

## Installation

```bash
pip install starlette-session
```

## Example

Using redis as backend

```python
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType

from redis import Redis

async def setup_session(request: Request) -> JSONResponse:
    request.session.update({"data": "session_data"})
    return JSONResponse({"session": request.session})


async def clear_session(request: Request):
    request.session.clear()
    return JSONResponse({"session": request.session})


def view_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": request.session})


routes = [
    Route("/setup_session", endpoint=setup_session),
    Route("/clear_session", endpoint=clear_session),
    Route("/view_session", endpoint=view_session),
]

redis_client = Redis(host="localhost", port=6379)
app = Starlette(debug=True, routes=routes)
app.add_middleware(
    SessionMiddleware,
    secret_key="secret",
    cookie_name="cookie22",
    backend_type=BackendType.redis,
    backend_client=redis_client,
)

```

You can find more example [here](https://github.com/auredentan/starlette-session/tree/master/examples)

## Using a custom backend

You can provide a custom backend to be used. This backend has simply to implement the interface ISessionBackend

```python
class ISessionBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError()

    @abstractmethod
    async def set(self, key: str, value: dict, exp_in_mins: str) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    async def delete(key: str) -> Any:
        raise NotImplementedError()
```