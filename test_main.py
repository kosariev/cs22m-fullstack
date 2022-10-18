import asyncio
import pytest

from typing import Generator
from fastapi.testclient import TestClient
from main import app
from models import User
from tortoise.contrib.test import finalizer, initializer


@pytest.fixture(scope="module")
def client() -> Generator:
    initializer(["models"])
    with TestClient(app) as c:
        yield c
    finalizer()


@pytest.fixture(scope="module")
def event_loop(client: TestClient) -> Generator:
    yield asyncio.get_event_loop()


def test_read_main(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_init_user(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get("/init/")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}

    async def get_user_by_db():
        user = await User.get(username="demo")
        return user

    user_obj = event_loop.run_until_complete(get_user_by_db())
    assert user_obj.username == "demo"


def test_security_oauth2(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get("/users/me", headers={"Authorization": "Bearer ZGVtbw=="})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "demo"}


def test_security_oauth2_password_bearer_incorrect(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get("/users/me", headers={"Authorization": "Bearer zgvTBW=="})
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Object does not exist"}


def test_security_oauth2_password_bearer_no_header(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}
