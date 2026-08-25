#!/usr/bin/env python3
"""
hash_name.py — print the SHA-256 hex of a normalized name/company.

Used to extend frontend-2/public/access.json. Normalization matches the
frontend gate (trim + lowercase) so hashes line up exactly.

Usage:
  python3 tools/hash_name.py jarek
  python3 tools/hash_name.py "BILLS"
"""
import hashlib
import sys


def normalize(value: str) -> str:
    return value.strip().lower()


def hash_value(value: str) -> str:
    return hashlib.sha256(normalize(value).encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("usage: python3 tools/hash_name.py <name-or-company>", file=sys.stderr)
        return 2
    print(hash_value(sys.argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
