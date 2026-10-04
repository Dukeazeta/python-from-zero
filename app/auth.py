"""Sign in with Google (OpenID Connect, authorization code flow with PKCE).

Docs: https://developers.google.com/identity/openid-connect/openid-connect
  1. /auth/google sends the browser to Google with a random `state`, a `nonce`, and a
     PKCE code challenge. The state is also put in a short-lived cookie, so the sign-in
     can only finish in the browser that started it.
  2. Google sends the browser back to /auth/callback with a one-time `code`.
  3. The server swaps the code for an ID token at Google's token endpoint. The token comes
     straight from Google over HTTPS, so (as Google's docs allow) its signature isn't
     re-checked here; its issuer, audience, expiry and nonce are.
"""

import base64
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ISSUERS = ("https://accounts.google.com", "accounts.google.com")


class SignInError(Exception):
    pass


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def new_request():
    """Fresh random values for one sign-in: (state, PKCE verifier, nonce)."""
    return secrets.token_urlsafe(32), secrets.token_urlsafe(48), secrets.token_urlsafe(24)


def authorize_url(client_id, redirect_uri, state, verifier, nonce, auth_url=AUTH_URL):
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    query = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    })
    return f"{auth_url}?{query}"


def exchange_code(client_id, client_secret, redirect_uri, code, verifier, token_url=TOKEN_URL):
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }).encode("ascii")
    req = urllib.request.Request(token_url, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SignInError(f"Google didn't accept the sign-in ({e.code}).") from e
    except urllib.error.URLError as e:
        raise SignInError("Couldn't reach Google to finish signing in.") from e


def read_id_token(id_token, client_id, nonce):
    """Check the ID token's claims and return them."""
    try:
        payload = id_token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError) as e:
        raise SignInError("Google sent back a sign-in token that couldn't be read.") from e
    if claims.get("iss") not in ISSUERS:
        raise SignInError("The sign-in token wasn't issued by Google.")
    if claims.get("aud") != client_id:
        raise SignInError("The sign-in token was meant for a different app.")
    if claims.get("exp", 0) < time.time():
        raise SignInError("The sign-in token has expired. Try again.")
    if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
        raise SignInError("The sign-in didn't match the one this browser started. Try again.")
    if not claims.get("sub"):
        raise SignInError("Google didn't say which account signed in.")
    if not claims.get("email_verified"):
        raise SignInError("That Google account's email address isn't verified.")
    return claims


def safe_next(path):
    """Only allow redirects back to a page on this site."""
    if isinstance(path, str) and path.startswith("/") and not path.startswith("//") and "\\" not in path:
        return path
    return "/"
