from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import requests
import time
import os

app = FastAPI(title="FastAPI + Keycloak (lab)")
bearer = HTTPBearer()

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_PORT = os.getenv("KEYCLOAK_PORT", "8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "myrealm")
REALM_URL = f"http://{KEYCLOAK_HOST}:{KEYCLOAK_PORT}/realms/{KEYCLOAK_REALM}"

_cached_pubkey = None
_cached_time = 0
_PUBKEY_TTL = 60 * 60  # seconds

def get_realm_public_key(force=False):
    global _cached_pubkey, _cached_time
    if _cached_pubkey and not force and (time.time() - _cached_time) < _PUBKEY_TTL:
        return _cached_pubkey

    resp = requests.get(REALM_URL, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to get realm info: {resp.status_code}")
    j = resp.json()
    pub_b64 = j.get("public_key")
    if not pub_b64:
        raise RuntimeError("realm public_key missing")
    pem = "-----BEGIN PUBLIC KEY-----\n"
    for i in range(0, len(pub_b64), 64):
        pem += pub_b64[i:i+64] + "\n"
    pem += "-----END PUBLIC KEY-----\n"
    _cached_pubkey = pem
    _cached_time = time.time()
    return pem

def verify_token_str(token: str):
    pub = get_realm_public_key()
    try:
        claims = jwt.decode(token, pub, algorithms=["RS256"], options={"verify_aud": False})
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")
    return claims

def get_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid auth scheme")
    return credentials.credentials

@app.get("/public")
def public():
    return {"msg": "public endpoint"}

@app.get("/private")
def private(token: str = Depends(get_token)):
    claims = verify_token_str(token)
    return {"msg": "protected", "claims": claims}

@app.get("/realm")
def realm():
    try:
        return requests.get(REALM_URL, timeout=8).json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
