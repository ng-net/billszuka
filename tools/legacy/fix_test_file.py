#!/usr/bin/env python3
"""Fix test_validate_columns.py — rebuild clean sections."""
import sys
sys.path.insert(0, str(__file__.rsplit("/", 1)[0]))

from pathlib import Path
path = str(Path(__file__).resolve().parent.parent / "tests" / "test_validate_columns.py")
with open(path, encoding="utf-8") as f:
    lines = f.readlines()

print(f"Current: {len(lines)} lines")

# Find TestSeparatorDetection
sep_idx = None
for i, l in enumerate(lines):
    if l.strip() == "class TestSeparatorDetection:":
        sep_idx = i
        print(f"TestSeparatorDetection at line {i+1}")
        break

# Replace lines 274 to sep_idx-1 with clean versions
# Build replacement for the broken section
replacement = [
    "    def test_clean_a_row_no_issues(self):\n",
    "        row = {\"kategoria\": \"A1\"}\n",
    "        issues = vc.cross_check(row, \"A\")\n",
    "        assert issues == []\n",
    "\n",
    "\n",
    "class TestSentinelNormalisation:\n",
    "    \"\"\"KNOW_NON_VALUE + normalize_non_value — provenance placeholders.\"\"\"\n",
    "\n",
    "    def test_known_sentinels_normalised_to_empty(self):\n",
    "        for sentinel in (\"brak\", \"n/a\", \"na\", \"nd\", \"nie\", \"no\",\n",
    "                         \"nie dotyczy\", \"do weryfikacji\", \"do ustalenia\",\n",
    '                         "do uzupe\\u0142nienia", "unknown", "\\u2014", "\\u2013", "-"):\n',
    '            assert vc.normalize_non_value(sentinel) == "", f"sentinel {sentinel!r} -> empty"\n',
    "\n",
    "    def test_non_sentinels_pass_through(self):\n",
    '        for value in ("PowerMatic", "wysoki", "https://example.com", "test@example.com",\n',
    '                      "+48 123 456 789", "PL", "mix"):\n',
    '            assert vc.normalize_non_value(value) == value.strip(), f"value {value!r} passes through"\n',
    "\n",
    "    def test_sentinel_on_enum_columns(self):\n",
    '        assert vc.validate_value("cross_sell_potential", "brak", "PL") == []\n',
    '        assert vc.validate_value("cross_sell_potential", "do ustalenia", "PL") == []\n',
    '        assert vc.validate_value("linkedin", "brak", "PL") == []\n',
    '        assert vc.validate_value("email_decydent", "n/a", "PL") == []\n',
    "\n",
    "\n",
]

# Replace lines[274:sep_idx] with replacement
# sep_idx should be the start of TestSeparatorDetection
lines[274:sep_idx] = replacement

print(f"After: {len(lines)} lines")
with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("Written")

# Verify syntax
import ast
with open(path, encoding="utf-8") as f:
    src = f.read()
try:
    ast.parse(src)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}: {e.msg}")
    lines_src = src.splitlines()
    for i in range(max(0, e.lineno-3), min(len(lines_src), e.lineno+2)):
        print(f"  {i+1}: {lines_src[i]}")
