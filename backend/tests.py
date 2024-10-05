import pytest
from fastapi.testclient import TestClient
from main import app
from database import models, db as database
from api.auth.utils import *  # noqa: F403

client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    yield db
    db.close()
    models.Base.metadata.drop_all(bind=database.engine)

def test_registration(test_db):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_login(test_db):
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_incorrect_login(test_db):
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_change_password(test_db):
    login_response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    access_token = login_response.json()["access_token"]

    response = client.post("/api/auth/change-password", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "current_password": "testpassword",
        "new_password": "newtestpassword"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    # Test if the old password doesn't work anymore
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 401

    # Test login with new password
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "newtestpassword"
    })
    assert response.status_code == 200

def test_reset_password(test_db):
    reset_token = create_reset_token({"sub": "testuser@example.com"})  # noqa: F405

    response = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "anothernewpassword"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"

    # Test login with the new reset password
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "anothernewpassword"
    })
    assert response.status_code == 200

    
def test_refresh_token(test_db):
    response = client.post("/api/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    refresh_token = response.json()["refresh_token"]

    response = client.post("/api/auth/token/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200, f"Response status code was {response.status_code} with response body {response.text}"
    data = response.json()
    assert "access_token" in data

def test_forgot_password(test_db):
    response = client.post("/api/auth/forgot-password", json={
        "email": "testuser@example.com"
    })
    assert response.status_code == 200, f"Response status code was {response.status_code} with response body {response.text}"
    assert response.json()["message"] == "If this email is registered, you will receive instructions to reset your password."

