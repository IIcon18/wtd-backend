"""Unit tests for app.core.security — no DB or network required."""
import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── hash_password / verify_password ──────────────────────────────────────────

def test_hash_differs_from_plain():
    assert hash_password("mypassword") != "mypassword"


def test_hash_has_reasonable_length():
    assert len(hash_password("x")) > 20


def test_hash_is_unique_per_call():
    """bcrypt uses a random salt, so two hashes of the same input must differ."""
    assert hash_password("same") != hash_password("same")


def test_verify_correct_password():
    hashed = hash_password("s3cr3t")
    assert verify_password("s3cr3t", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("s3cr3t")
    assert verify_password("wrong", hashed) is False


def test_verify_empty_password_against_nonempty_hash():
    hashed = hash_password("nonempty")
    assert verify_password("", hashed) is False


# ── create_access_token / decode_token ───────────────────────────────────────

def test_access_token_payload():
    token = create_access_token(user_id=42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


def test_access_tokens_have_unique_jti():
    t1 = create_access_token(1)
    t2 = create_access_token(1)
    assert decode_token(t1)["jti"] != decode_token(t2)["jti"]


# ── create_refresh_token ─────────────────────────────────────────────────────

def test_refresh_token_payload():
    token, jti = create_refresh_token(user_id=7)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti


def test_refresh_token_returns_matching_jti():
    token, jti = create_refresh_token(99)
    assert decode_token(token)["jti"] == jti


# ── decode_token edge cases ───────────────────────────────────────────────────

def test_decode_invalid_string():
    assert decode_token("not.a.valid.token") is None


def test_decode_garbage():
    assert decode_token("garbage") is None


def test_decode_wrong_secret():
    payload = {"sub": "1", "type": "access", "exp": 9_999_999_999}
    bad_token = jwt.encode(payload, "wrong-secret", algorithm=settings.ALGORITHM)
    assert decode_token(bad_token) is None


def test_decode_empty_string():
    assert decode_token("") is None
