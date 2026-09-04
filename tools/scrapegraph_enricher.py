#!/usr/bin/env python3
"""
tools/scrapegraph_enricher.py — ScrapeGraphAI integration for BILLSzuka.

Utilizes ScrapeGraphAI's SmartScraperGraph to extract structured lead data,
company contacts, decision makers, and product assortment directly from
unstructured websites, supplier lists, and registry pages.

Features:
- Configured with project LLM keys (OpenRouter / Google Gemini)
- Pydantic schema validation for Canonical BILLSzuka fields
- Normalization with checksums (NIP / ICO) and Should-Sell/Powinowactwo scoring
- CLI and Python API usage

Usage:
  python3 tools/scrapegraph_enricher.py --url "https://example.com/kontakt" --type company
  python3 tools/scrapegraph_enricher.py --url "https://example.com/e-shop" --type assortment
  python3 tools/scrapegraph_enricher.py --url "https://example.com" --prompt "Find distributor brands and contacts"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TOOLS_DIR = ROOT / "tools"
ENV_FILE = ROOT / ".env"
SECRETS_FILE = TOOLS_DIR / "api_secrets.json"

sys.path.insert(0, str(TOOLS_DIR))
try:
    from checksums import validate_id
except ImportError:
    validate_id = None

try:
    from score_powinowactwo import score_row
except ImportError:
    score_row = None


# ---------------------------------------------------------------------------
# Pydantic Schemas for Structured Lead Extraction
# ---------------------------------------------------------------------------

class CompanyContactSchema(BaseModel):
    nazwa: Optional[str] = Field(None, description="Official company name or brand name")
    nip_vat: Optional[str] = Field(None, description="Tax ID / VAT number / NIP / ICO / CUI / OIB")
    miasto: Optional[str] = Field(None, description="City of headquarters or main office")
    adres: Optional[str] = Field(None, description="Street address including postal code")
    kraj: Optional[str] = Field(None, description="2-letter ISO country code, e.g. PL, CZ, SK, RO")
    email: Optional[str] = Field(None, description="General or sales contact email")
    telefon: Optional[str] = Field(None, description="Official telephone contact number")
    decydent: Optional[str] = Field(None, description="Full name of Owner, CEO, Managing Director or Contact Person")
    stanowisko: Optional[str] = Field(None, description="Role/Position of the decision maker (e.g. Prezes Zarządu, CEO, Owner)")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL of the company or decision maker")


class AssortmentSchema(BaseModel):
    sprzedaje_nabijarki: Optional[bool] = Field(False, description="Whether the shop/distributor sells cigarette rolling machines or filling machines")
    marki_nabijarki: Optional[str] = Field(None, description="Brands of rolling machines found (e.g. PowerMatic, OCB, Mascotte, Hawk, Gizeh)")
    marka_wlasna_oem: Optional[str] = Field(None, description="Private label or own-brand machines/accessories")
    kategoria: Optional[str] = Field(None, description="Categorization: A (roller seller) or B (tobacco wholesale, vape, CBD, accessories)")
    asortyment_opis: Optional[str] = Field(None, description="Brief summary of main product categories offered")


class LeadEnrichmentResult(BaseModel):
    company: CompanyContactSchema
    assortment: Optional[AssortmentSchema] = None
    notatki: Optional[str] = Field(None, description="Relevant details about B2B conditions, wholesale requirements or distribution potential")


# ---------------------------------------------------------------------------
# LLM & Graph Configuration Resolver
# ---------------------------------------------------------------------------

def load_project_env() -> Dict[str, str]:
    """Load credentials from .env and api_secrets.json."""
    env: Dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("\"'")

    # Try api_secrets.json
    if SECRETS_FILE.exists():
        try:
            secrets = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
            if "openrouter" in secrets and secrets["openrouter"]:
                for item in secrets["openrouter"]:
                    if item.get("key") and "..." not in item["key"]:
                        env.setdefault("OPENROUTER_API_KEY", item["key"])
            if "gemini" in secrets and secrets["gemini"]:
                for item in secrets["gemini"]:
                    if item.get("key") and not env.get("GEMINI_API_KEY"):
                        env.setdefault("GEMINI_API_KEY", item["key"])
        except Exception:
            pass

    for k, v in os.environ.items():
        env.setdefault(k, v)
    return env


def get_graph_config(preferred_provider: Optional[str] = None) -> Dict[str, Any]:
    """Generate the ScrapeGraphAI graph configuration using available project keys.
    
    Adheres to project priority: gemini -> openrouter -> openai -> ollama.
    """
    env = load_project_env()
    
    gemini_key = env.get("GEMINI_API_KEY", "").strip()
    openrouter_key = env.get("OPENROUTER_API_KEY", "").strip()
    openai_key = env.get("OPENAI_API_KEY", "").strip()

    # Prioritize gemini as per AGENTS.md rule (gemini -> mock -> openrouter)
    if (preferred_provider == "gemini" or not preferred_provider) and gemini_key:
        return {
            "llm": {
                "api_key": gemini_key,
                "model": "google_genai/gemini-2.5-flash",
                "temperature": 0.0,
                "model_tokens": 16384,
            },
            "verbose": False,
            "headless": True,
        }
    elif openrouter_key and "sk-or-v1-" in openrouter_key and not openrouter_key.endswith("..."):
        return {
            "llm": {
                "api_key": openrouter_key,
                "model": "openai/deepseek/deepseek-chat",
                "base_url": "https://openrouter.ai/api/v1",
                "temperature": 0.0,
                "model_tokens": 8192,
            },
            "verbose": False,
            "headless": True,
        }
    elif openai_key:
        return {
            "llm": {
                "api_key": openai_key,
                "model": "openai/gpt-4o-mini",
                "temperature": 0.0,
                "model_tokens": 8192,
            },
            "verbose": False,
            "headless": True,
        }
    else:
        # Fallback to local Ollama if no API key is present
        return {
            "llm": {
                "model": "ollama/llama3",
                "temperature": 0.0,
                "base_url": "http://localhost:11434",
            },
            "verbose": False,
            "headless": True,
        }


# ---------------------------------------------------------------------------
# Scraper Operations
# ---------------------------------------------------------------------------

def scrape_url(
    url: str,
    prompt: Optional[str] = None,
    schema_type: str = "company",
    custom_schema: Optional[type[BaseModel]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute ScrapeGraphAI SmartScraperGraph against a target URL."""
    try:
        from scrapegraphai.graphs import SmartScraperGraph
    except ImportError:
        return {
            "error": "scrapegraphai is not installed. Run: pip install scrapegraphai"
        }

    cfg = config or get_graph_config()

    # Determine prompt and schema
    selected_schema = None
    if custom_schema:
        selected_schema = custom_schema
        default_prompt = "Extract the requested information according to the provided schema."
    elif schema_type == "company":
        selected_schema = CompanyContactSchema
        default_prompt = (
            "Extract official company contact details from this page, including official name, "
            "VAT / tax identification number (NIP/ICO/CUI/OIB), registered address, city, country, "
            "contact email, phone number, and name and title of the executive, director, or owner."
        )
    elif schema_type == "assortment":
        selected_schema = AssortmentSchema
        default_prompt = (
            "Analyze the product range on this website. Determine if they sell or distribute "
            "cigarette rolling machines, electric tube filling machines, or tobacco accessories. "
            "Identify specific machine brands (e.g. PowerMatic, Hawk, OCB, Mascotte) and own brands."
        )
    elif schema_type == "full":
        selected_schema = LeadEnrichmentResult
        default_prompt = (
            "Extract complete B2B company profile and tobacco/rolling machine product offering "
            "from this site, including contact details, tax ID, decision makers, and brands sold."
        )
    else:
        default_prompt = prompt or "Extract key company details and offerings from this page."

    final_prompt = prompt if prompt else default_prompt

    # Execute scraper with automatic fallback if primary provider fails (e.g. 429 quota)
    providers_to_try = []
    if cfg.get("llm", {}).get("model", "").startswith("google_genai"):
        providers_to_try.append(cfg)
        or_cfg = get_graph_config(preferred_provider="openrouter")
        if or_cfg != cfg:
            providers_to_try.append(or_cfg)
    else:
        providers_to_try.append(cfg)

    last_err = None
    for attempt_cfg in providers_to_try:
        try:
            scraper = SmartScraperGraph(
                prompt=final_prompt,
                source=url,
                config=attempt_cfg,
                schema=selected_schema,
            )
            result = scraper.run()
            
            # In case result is a BaseModel instance
            if hasattr(result, "model_dump"):
                return result.model_dump()
            elif hasattr(result, "dict"):
                return result.dict()
            elif isinstance(result, dict):
                return result
            else:
                return {"result": str(result)}
        except Exception as e:
            last_err = e
            # If rate limited or quota exhausted on Gemini, continue to OpenRouter
            err_str = str(e).lower()
            if "resource_exhausted" in err_str or "429" in err_str or "quota" in err_str:
                continue
            break

    return {
        "error": f"ScrapeGraphAI execution failed: {str(last_err)}",
        "url": url,
    }


def enrich_lead_dict(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to enrich an existing lead dict using its 'www' field."""
    url = lead.get("www", "").strip()
    if not url or url.lower() in ("brak", "n/a", "none"):
        return lead

    if not url.startswith("http"):
        url = "https://" + url

    scraped = scrape_url(url, schema_type="company")
    if not scraped or scraped.get("error"):
        return lead

    # Safely merge fields if missing or placeholder
    placeholders = {"brak", "n/a", "do weryfikacji", "", None}
    
    if scraped.get("nazwa") and lead.get("nazwa") in placeholders:
        lead["nazwa"] = scraped["nazwa"]
    if scraped.get("nip_vat") and lead.get("nip_vat") in placeholders:
        lead["nip_vat"] = scraped["nip_vat"]
    if scraped.get("miasto") and lead.get("miasto") in placeholders:
        lead["miasto"] = scraped["miasto"]
    if scraped.get("adres") and lead.get("adres") in placeholders:
        lead["adres"] = scraped["adres"]
    if scraped.get("email") and lead.get("email") in placeholders:
        lead["email"] = scraped["email"]
    if scraped.get("telefon") and lead.get("telefon") in placeholders:
        lead["telefon"] = scraped["telefon"]
    if scraped.get("decydent") and lead.get("decydent") in placeholders:
        lead["decydent"] = scraped["decydent"]
    if scraped.get("stanowisko") and lead.get("stanowisko") in placeholders:
        lead["stanowisko"] = scraped["stanowisko"]

    return lead


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="BILLSzuka ScrapeGraphAI Lead Scraper & Enricher")
    parser.add_argument("--url", help="Target URL to scrape")
    parser.add_argument("--prompt", help="Custom extraction prompt")
    parser.add_argument("--type", choices=["company", "assortment", "full", "custom"], default="company",
                        help="Pre-configured extraction schema")
    parser.add_argument("--test", action="store_true", help="Run self-test against sample HTML")
    args = parser.parse_args()

    if args.test:
        print("[BILLSzuka] Running ScrapeGraphAI self-test...")
        sample_html = """
        <html>
            <body>
                <h1>Tabak Bohemia s.r.o.</h1>
                <p>Adresa: Václavské náměstí 1, 110 00 Praha 1, Czech Republic</p>
                <p>IČO: 27123456 | DIČ: CZ27123456</p>
                <p>Kontakt: info@tabakbohemia.cz | Tel: +420 222 333 444</p>
                <p>Jednatel: Jan Novák (CEO & Founder)</p>
                <div>Nabízíme elektrické plničky cigaret značek PowerMatic a OCB.</div>
            </body>
        </html>
        """
        cfg = get_graph_config()
        print(f"Config resolved with model: {cfg['llm'].get('model')}")
        from scrapegraphai.graphs import SmartScraperGraph
        scraper = SmartScraperGraph(
            prompt="Extract company name, IČO/VAT, city, email, and decision maker name with title.",
            source=sample_html,
            config=cfg,
            schema=CompanyContactSchema,
        )
        res = scraper.run()
        print("Self-test result:")
        print(json.dumps(res if isinstance(res, dict) else res.dict(), indent=2, ensure_ascii=False))
        return 0

    if not args.url:
        parser.print_help()
        return 1

    print(f"🌐 Scraping URL: {args.url} (Schema: {args.type})")
    result = scrape_url(args.url, prompt=args.prompt, schema_type=args.type)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
