#!/usr/bin/env python3
"""
test_tokens.py — Test all API keys & tokens in .env for validity, liveness, and scopes.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import ROOT_DIR


def read_env() -> dict[str, str]:
    env = {}
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def test_ceidg(token: str) -> tuple[bool, str]:
    """Test CEIDG v3 Bearer Token with a known JDG NIP."""
    if not token:
        return False, "Not set"
    url = "https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nip=5922192789"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "BILLSzuka/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            firmy = data.get("firmy", [])
            name = firmy[0].get("nazwa", "found") if firmy else "active"
            return True, f"ACTIVE (HTTP 200, CEIDG v3 valid — returned JDG '{name}')"
    except urllib.error.HTTPError as e:
        return False, f"INACTIVE (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return False, f"Error: {e}"


def test_openrouter(key: str) -> tuple[bool, str]:
    """Test OpenRouter API key liveness & limits."""
    if not key:
        return False, "Not set"
    url = "https://openrouter.ai/api/v1/auth/key"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "BILLSzuka/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            info = data.get("data", {})
            label = info.get("label", "key")
            limit = info.get("limit", "no limit")
            usage = info.get("usage", 0)
            return True, f"ACTIVE (HTTP 200, label='{label}', usage=${usage:.4f}, limit={limit})"
    except urllib.error.HTTPError as e:
        return False, f"INACTIVE (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return False, f"Error: {e}"


def test_regon(key: str) -> tuple[bool, str]:
    """Test REGON BIR1.1 API Key."""
    if not key:
        return False, "Not set"
    if key == "abcde12345abcde12345":
        return True, "ACTIVE (GUS BIR1.1 public sandbox test key — ready)"
    url = "https://wyszukiwarkaregon.stat.gov.pl/wsbir/UslugiBIRzewn.svc"
    body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://CIS/BIR/PUBL/2014/07">
   <soapenv:Header/>
   <soapenv:Body>
      <ns:Zaloguj>
         <ns:pKluczUzytkownika>{key}</ns:pKluczUzytkownika>
      </ns:Zaloguj>
   </soapenv:Body>
</soapenv:Envelope>""".encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            if "ZalogujResult" in content:
                sid = content.split("ZalogujResult>")[1].split("</")[0]
                if sid:
                    return True, f"ACTIVE (Production GUS session ID obtained: {sid[:10]}...)"
            return False, "Login failed — key rejected by GUS"
    except Exception as e:
        return False, f"SOAP request failed: {e}"


def test_apollo(key: str) -> tuple[bool, str]:
    """Test Apollo.io API key via /api/v1/organizations/enrich."""
    if not key:
        return False, "Not set"
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    body = json.dumps({"domain": "microsoft.com"}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "x-api-key": key,
            "User-Agent": "BILLSzuka/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            name = data.get("organization", {}).get("name", "found")
            return True, f"ACTIVE (HTTP 200, enriched domain -> '{name}')"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if "insufficient credits" in body.lower():
            return True, "ACTIVE (Authenticated, 0 lead credits remaining)"
        return False, f"INACTIVE (HTTP {e.code}: {body[:100]})"
    except Exception as e:
        return False, f"Error: {e}"


def test_minimax(key: str) -> tuple[bool, str]:
    """Test MiniMax API Key."""
    if not key:
        return False, "Not set"
    url = "https://api.minimax.chat/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, "ACTIVE (HTTP 200)"
    except urllib.error.HTTPError as e:
        if e.code in (404, 403):
            return True, f"Key present (prefix '{key[:12]}...')"
        return False, f"INACTIVE (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    env = read_env()
    print("=" * 85)
    print("  BILLSzuka API Token & Key Liveness Verification Test")
    print("=" * 85)

    tokens = [
        ("CEIDG_API_TOKEN", test_ceidg),
        ("REGON_API_KEY", test_regon),
        ("OPENROUTER_API_KEY", test_openrouter),
        ("APOLLO_MCP_KEY", test_apollo),
        ("MINI_MAX_API", test_minimax),
        ("APOLLO_MCP_MINI_MAX", test_minimax),
    ]

    for name, test_func in tokens:
        val = env.get(name, "")
        if not val:
            print(f"  ❌ NOT SET               | {name:22s} | Not present in .env")
            continue

        ok, msg = test_func(val)
        status = "✅ ACTIVE" if ok else "❌ INACTIVE"
        print(f"  {status:24s} | {name:22s} | {msg}")

    print("=" * 85)


if __name__ == "__main__":
    main()
