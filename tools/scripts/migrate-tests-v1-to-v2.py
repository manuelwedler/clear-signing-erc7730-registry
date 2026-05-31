#!/usr/bin/env python3
"""
Migrate legacy `tests/<X>.tests.json` files (v1, flat `expectedTexts`)
to `testsv2/<X>.tests.json` (v2, structured `expected`).

INTERNAL ONE-SHOT TOOL — not committed.

Usage:
    /tmp/migrate-tests-venv/bin/python3 tools/scripts/migrate-tests-v1-to-v2.py --entity <name>
    /tmp/migrate-tests-venv/bin/python3 tools/scripts/migrate-tests-v1-to-v2.py --file <path>
"""

import argparse
import json
<<<<<<< Updated upstream
import re
import sys
import traceback
from pathlib import Path

from eth_utils import keccak
=======
import os
import re
import sys
import traceback
import urllib.parse
import urllib.request
from pathlib import Path

from eth_utils import keccak, to_checksum_address
>>>>>>> Stashed changes
from eth_abi import decode as abi_decode
import rlp


# ---------------------------------------------------------------------------
<<<<<<< Updated upstream
=======
# Etherscan token metadata lookup (cached on disk)
# ---------------------------------------------------------------------------

_TOKEN_CACHE_PATH = Path(__file__).resolve().parent / ".token-cache.json"
_TOKEN_CACHE = None


def _load_token_cache():
    global _TOKEN_CACHE
    if _TOKEN_CACHE is not None:
        return _TOKEN_CACHE
    if _TOKEN_CACHE_PATH.exists():
        try:
            _TOKEN_CACHE = json.loads(_TOKEN_CACHE_PATH.read_text())
        except Exception:
            _TOKEN_CACHE = {}
    else:
        _TOKEN_CACHE = {}
    return _TOKEN_CACHE


def _save_token_cache():
    if _TOKEN_CACHE is None:
        return
    _TOKEN_CACHE_PATH.write_text(json.dumps(_TOKEN_CACHE, indent=2, sort_keys=True))


_ETHERSCAN_API_KEY = "QPU28Q4AHZZ4HGFYWCMMTURT7WWSI8ZH7P"  # internal-only; this script is gitignored


def _etherscan_eth_call(chain_id, to, data):
    """Wrap eth_call via Etherscan's V2 multichain proxy. Returns hex result
    or None on error."""
    api_key = _ETHERSCAN_API_KEY or os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        return None
    params = {
        "chainid": str(chain_id),
        "module": "proxy",
        "action": "eth_call",
        "to": to,
        "data": data,
        "tag": "latest",
        "apikey": api_key,
    }
    url = "https://api.etherscan.io/v2/api?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = json.loads(resp.read().decode())
    except Exception:
        return None
    result = body.get("result")
    if isinstance(result, str) and result.startswith("0x"):
        return result
    return None


def _decode_abi_string(hex_str):
    """Decode an ABI-encoded `string` (or fall back to a bytes32 of ASCII
    with trailing zeros — some legacy tokens like MKR return bytes32)."""
    if not hex_str or not hex_str.startswith("0x"):
        return None
    h = hex_str[2:]
    # Standard string return: offset (32B) + length (32B) + padded data
    if len(h) >= 128:
        try:
            offset = int(h[:64], 16)
            length = int(h[64:128], 16)
            if offset == 32 and length > 0 and 128 + length * 2 <= len(h):
                data = bytes.fromhex(h[128:128 + length * 2])
                return data.decode("utf-8", errors="replace")
        except Exception:
            pass
    # bytes32 fallback (e.g. MKR): 64 hex chars of ASCII + nulls
    if len(h) == 64:
        try:
            return bytes.fromhex(h).rstrip(b"\x00").decode("utf-8", errors="replace")
        except Exception:
            pass
    return None


def _decode_uint(hex_str):
    if not hex_str or not hex_str.startswith("0x") or len(hex_str) < 3:
        return None
    try:
        return int(hex_str[2:], 16)
    except ValueError:
        return None


_NATIVE_SENTINELS = {
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "0x0000000000000000000000000000000000000000",
}

# Tokens on chains where the free Etherscan plan can't reach (e.g. BSC).
# Keyed by "<chainId>:<address-lower>".
_TOKEN_OVERRIDES = {
    "56:0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": {"symbol": "BUSD", "decimals": 18, "name": "BUSD Token"},
    "56:0x55d398326f99059ff775485246999027b3197955": {"symbol": "USDT", "decimals": 18, "name": "Tether USD"},
}


def lookup_token_metadata(address, chain_id):
    """Return {symbol, decimals, name} for the ERC-20 at `address` on
    `chain_id`. Uses a JSON cache on disk; falls back to TODO stub if the
    Etherscan call fails or no API key is set."""
    address = address.lower()
    if address in _NATIVE_SENTINELS:
        # DEX routers use these as "native chain currency" placeholders.
        # Chain 1/Arbitrum/etc all use ETH; override per chain when needed.
        return {"symbol": "ETH", "decimals": 18, "name": "Ether"}
    key = f"{chain_id}:{address}"
    if key in _TOKEN_OVERRIDES:
        return _TOKEN_OVERRIDES[key]
    cache = _load_token_cache()
    if key in cache:
        return cache[key]

    symbol = _decode_abi_string(_etherscan_eth_call(chain_id, address, "0x95d89b41"))
    decimals = _decode_uint(_etherscan_eth_call(chain_id, address, "0x313ce567"))
    name = _decode_abi_string(_etherscan_eth_call(chain_id, address, "0x06fdde03"))

    if symbol is None and decimals is None and name is None:
        # Avoid caching a complete failure — let the next run retry.
        return {"symbol": "TODO", "decimals": 0, "name": "TODO"}

    meta = {
        "symbol": symbol or "TODO",
        "decimals": decimals if decimals is not None else 0,
        "name": name or "TODO",
    }
    cache[key] = meta
    _save_token_cache()
    return meta


# ---------------------------------------------------------------------------
>>>>>>> Stashed changes
# Transaction decoding
# ---------------------------------------------------------------------------

def decode_signed_tx(hex_str):
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    raw = bytes.fromhex(hex_str)
    if raw[0] == 0x02:  # EIP-1559
        d = rlp.decode(raw[1:])
        return {
            "chainId": int.from_bytes(d[0], "big") if d[0] else 0,
            "to": "0x" + d[5].hex(),
            "value": int.from_bytes(d[6], "big") if d[6] else 0,
            "data": "0x" + d[7].hex(),
        }
    elif raw[0] == 0x01:  # EIP-2930
        d = rlp.decode(raw[1:])
        return {
            "chainId": int.from_bytes(d[0], "big") if d[0] else 0,
            "to": "0x" + d[4].hex(),
            "value": int.from_bytes(d[5], "big") if d[5] else 0,
            "data": "0x" + d[6].hex(),
        }
    else:  # legacy
        d = rlp.decode(raw)
<<<<<<< Updated upstream
        return {
            "chainId": None,
=======
        v = int.from_bytes(d[6], "big") if len(d) > 6 and d[6] else 0
        r = int.from_bytes(d[7], "big") if len(d) > 7 and d[7] else 0
        s = int.from_bytes(d[8], "big") if len(d) > 8 and d[8] else 0
        if v >= 37 and (r or s):
            # EIP-155 signed: v = chainId*2 + 35 + parity
            chain_id = (v - 35) // 2
        elif r == 0 and s == 0 and v >= 1:
            # EIP-155 pre-signing encoding: [..., chainId, 0, 0]
            chain_id = v
        else:
            # Pre-EIP-155 signed (v=27/28), no chainId in tx
            chain_id = None
        return {
            "chainId": chain_id,
>>>>>>> Stashed changes
            "to": "0x" + d[3].hex(),
            "value": int.from_bytes(d[4], "big") if d[4] else 0,
            "data": "0x" + d[5].hex(),
        }


# ---------------------------------------------------------------------------
# Signature parsing
# ---------------------------------------------------------------------------

_WS_SPLIT = re.compile(r"\s+")


def _split_top_commas(s):
    out, depth, buf = [], 0, []
    for ch in s:
        if ch == "(":
            depth += 1; buf.append(ch)
        elif ch == ")":
            depth -= 1; buf.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


def _parse_arg(s):
    """Parse one function-signature arg, returning (canonical_type, name_or_None).

    Handles plain types, arrays, and nested tuples — strips names from inner
    tuple elements so the canonical type matches what keccak expects.
    """
    s = s.strip()
    if not s:
        return ("", None)
    if s.startswith("("):
        depth = 0
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    inner = s[1:i]
                    inner_canon = ",".join(_parse_arg(p)[0] for p in _split_top_commas(inner))
                    rest = s[i + 1 :].strip()
                    arr = ""
                    m = re.match(r"((?:\[\d*\])+)", rest)
                    if m:
                        arr = m.group(1)
                        rest = rest[len(arr) :].strip()
                    return (f"({inner_canon}){arr}", rest or None)
        return (s, None)
    toks = _WS_SPLIT.split(s)
    if len(toks) == 1:
        return (toks[0], None)
    return (toks[0], toks[-1])


def parse_signature(sig_with_names):
    paren = sig_with_names.find("(")
    name = sig_with_names[:paren]
    inside = sig_with_names[paren + 1 : sig_with_names.rfind(")")]
    if not inside.strip():
        return name, []
    return name, [_parse_arg(p) for p in _split_top_commas(inside)]


def canonical_signature(sig_with_names):
    name, params = parse_signature(sig_with_names)
    return f"{name}({','.join(t for t, _ in params)})"


def function_selector(sig_with_names):
    return keccak(canonical_signature(sig_with_names).encode())[:4]


# ---------------------------------------------------------------------------
# expectedTexts cleanup + heuristics
# ---------------------------------------------------------------------------

# Words that frequently start a descriptor field label. Used to detect
# label boundaries when the descriptor doesn't tell us what labels exist.
COMMON_LABEL_STARTS = {
    "Amount", "Min", "Minimum", "Max", "Maximum",
    "For", "To", "From", "On", "Of",
    "Spender", "Recipient", "Receiver", "Sender", "Owner", "Debtor", "Holder",
    "Token", "Asset", "Tokens", "Assets", "Currency",
    "Order", "Orders",
    "Permit", "Signature", "Sig",
    "Deadline", "Expiry", "Expiration",
    "Nonce",
    "Collateral", "Debt", "Interest", "Rate",
    "Fee", "Fees", "Gas",
    "Approve", "Transfer", "Swap", "Deposit", "Borrow", "Repay", "Withdraw", "Stake", "Unstake", "Claim",
    "Reward", "Rewards",
    "Validator", "Operator", "Delegate",
    "Source", "Destination", "Path", "Route",
    "Slippage", "Tolerance", "Threshold",
    "Buy", "Sell", "Trade",
    "Beneficiary", "Initiator",
    "Position", "Margin", "Leverage",
    "Memo", "Note", "Reason",
    "Period", "Duration", "Window",
    "Maker", "Taker",
    "Quantity", "Limit", "Quantity",
    "Strike", "Premium",
}


def merge_ocr_fragments(texts):
<<<<<<< Updated upstream
    """Combine ['R', 'eview…'] → ['Review…']."""
=======
    """Combine word fragments split across Ledger screens.

    The signature is a short capitalised prefix (1-3 chars) followed by an
    entry that starts with a lowercase letter. Examples:
      ['R', 'eview transaction to Swap'] -> ['Review transaction to Swap']
      ['To', 'kenID 0']                  -> ['TokenID 0']
    """
>>>>>>> Stashed changes
    out, i = [], 0
    while i < len(texts):
        if (
            i + 1 < len(texts)
<<<<<<< Updated upstream
            and len(texts[i]) == 1
            and texts[i].isalpha()
            and texts[i].isupper()
=======
            and 1 <= len(texts[i]) <= 3
            and texts[i].isalpha()
            and texts[i][0].isupper()
>>>>>>> Stashed changes
            and texts[i + 1]
            and texts[i + 1][0].islower()
        ):
            out.append(texts[i] + texts[i + 1])
            i += 2
        else:
            out.append(texts[i])
            i += 1
    return out


def strip_noise(texts):
    """Drop standalone single-letter tokens (Ledger 'R' page markers), 'Swipe to review' suffix, etc."""
    cleaned = []
    for t in texts:
        if not t:
            continue
        # Drop single-letter alphabetic standalone tokens.
        if len(t) == 1 and t.isalpha():
            continue
        # Trim trailing "Swipe to review" cruft.
        t = re.sub(r"\s*Swipe to review\s*$", "", t).strip()
        if t:
            cleaned.append(t)
    return cleaned


def dedupe_adjacent(texts):
    """Collapse identical consecutive entries (Ledger shows same screen across pages)."""
    out = []
    for t in texts:
        if not out or out[-1] != t:
            out.append(t)
    return out


def drop_max_fees(texts):
    """Remove 'Max fees' followed by its value entry. Ledger UI artifact."""
    out, i = [], 0
    while i < len(texts):
        if texts[i] == "Max fees":
            i += 2  # skip 'Max fees' and the next value
            continue
        out.append(texts[i])
        i += 1
    return out


def looks_like_address_with_spaces(s):
    return bool(re.fullmatch(r"0x[0-9A-Fa-f]+(?:\s+[0-9A-Fa-f]+)+", s))


def looks_like_value_start(word):
    """Heuristic: a word that's almost certainly the start of a VALUE rather than a label."""
    if not word:
        return False
    if word[0].isdigit():
        return True
    if word.startswith("0x") and len(word) > 4:
        return True
    if word.startswith("$"):
        return True
    if word in ("All", "Any", "None"):  # threshold magic words from descriptors
        return True
    if word == "???":
        return True
    return False


_NETWORK_SUFFIX_RE = re.compile(r"\s+Network\s+[A-Z][A-Za-z0-9\- ]*$")


def strip_network_suffix(v):
    """Drop Ledger's trailing ' Network <ChainName>' UI element from a value."""
    return _NETWORK_SUFFIX_RE.sub("", v).strip()


def merge_digit_grouping(v):
    """Merge Ledger's digit-grouping spaces inside a decimal number.

    Examples:
      '76.2346524355882 10907 sAVAX' -> '76.234652435588210907 sAVAX'
      '0.0040999999999999 99 ETH'    -> '0.004099999999999999 ETH'
      '4303.00000000000 0262144 $MBG' -> '4303.000000000000262144 $MBG'

    Pattern: a run of digit groups separated by single spaces, optionally
    followed by a non-numeric token (the unit). Only collapses when the
    leading group contains a decimal point — that's the Ledger pattern.
    """
    parts = v.split()
    if len(parts) < 2:
        return v
<<<<<<< Updated upstream
    # Walk: collect a run of digit-only tokens following an initial decimal number.
    if not re.fullmatch(r"\d+\.\d+", parts[0]):
        return v
    merged = parts[0]
    i = 1
    while i < len(parts) and parts[i].isdigit():
        merged += parts[i]
        i += 1
    return " ".join([merged] + parts[i:])
=======
    # Walk every position; merge any run of digit groups (including integer-only
    # sequences like '100000000000000000 0' -> '1000000000000000000') where the
    # first token is a decimal/integer and the followers are pure digits.
    out = []
    i = 0
    while i < len(parts):
        if re.fullmatch(r"\d+(\.\d+)?", parts[i]):
            j = i + 1
            while j < len(parts) and parts[j].isdigit():
                j += 1
            if j > i + 1:
                out.append("".join(parts[i:j]))
                i = j
                continue
        out.append(parts[i])
        i += 1
    return " ".join(out)
>>>>>>> Stashed changes


def clean_value(v):
    if not isinstance(v, str):
        return v
    if looks_like_address_with_spaces(v):
        return re.sub(r"\s+", "", v)
    v = strip_network_suffix(v)
    v = merge_digit_grouping(v)
    return v


_REVIEW_TX_RE = re.compile(r"^[Rr]eview transaction to (.+?)$")


def extract_intent(merged):
    """Return the first '... transaction to X' tail if any, else None."""
    for t in merged:
        m = _REVIEW_TX_RE.match(t)
        if m:
            return m.group(1).strip()
    return None


def split_owner_from_first(first_entry, known_labels=None):
    """Split a possibly-concatenated first entry into (owner, remaining_text_starting_at_label).

    The first entry after 'Interaction with' often looks like:
        "1inch Network Amount to Send 4303... $MBG Minimum to"
    where the owner ("1inch Network") is glued to the start of the first field.
    Find the earliest label-start word and split there.
    """
    if not first_entry:
        return "", ""
    # Prefer known labels if available — split at the first one that occurs.
    if known_labels:
        earliest_idx, earliest_label = len(first_entry), None
        for lbl in known_labels:
            idx = first_entry.find(lbl)
            if 0 <= idx < earliest_idx:
                earliest_idx, earliest_label = idx, lbl
        if earliest_label is not None:
            return first_entry[:earliest_idx].strip(), first_entry[earliest_idx:].strip()
    # Fallback: split on first COMMON_LABEL_STARTS word.
    words = first_entry.split()
    for i, w in enumerate(words):
        if w in COMMON_LABEL_STARTS:
            return " ".join(words[:i]).strip(), " ".join(words[i:]).strip()
    return first_entry.strip(), ""


def parse_label_value_chunks(text, known_labels=None):
    """Walk a concatenated string, emit {label: value} dict.

    Two strategies:
      - If `known_labels` is provided: anchor split at known-label positions
        (longest first to avoid partial matches).
      - Else: walk word-by-word, treat each occurrence of a COMMON_LABEL_STARTS
        word as the start of a new label; absorb following words into the label
        until we hit a value-start word, then absorb the rest into the value
        until we hit the next label start.
    """
    fields = {}
    if not text:
        return fields

    if known_labels:
        # Anchor on known labels.
        sorted_lbls = sorted(known_labels, key=lambda x: -len(x))
        boundaries = []
        i = 0
        while i < len(text):
            matched = False
            for lbl in sorted_lbls:
                if text.startswith(lbl, i):
                    boundaries.append((i, lbl))
                    i += len(lbl)
                    matched = True
                    break
            if not matched:
                i += 1
        for j, (start, lbl) in enumerate(boundaries):
            value_start = start + len(lbl)
            value_end = boundaries[j + 1][0] if j + 1 < len(boundaries) else len(text)
            value = text[value_start:value_end].strip()
            fields[lbl] = clean_value(value) if value else "TODO"
        # Ensure all known labels appear, even if not found.
        for lbl in known_labels:
            fields.setdefault(lbl, "TODO")
        return fields

    # No known labels — heuristic walk.
    words = text.split()
    i = 0
    while i < len(words):
        if words[i] in COMMON_LABEL_STARTS:
            # Found the start of a candidate label. Absorb words until value-start.
            label_words = [words[i]]
            j = i + 1
            while j < len(words) and not looks_like_value_start(words[j]):
                label_words.append(words[j])
                j += 1
            label = " ".join(label_words).strip()
            # Absorb value words until next COMMON_LABEL_STARTS that's not value-start.
            value_words = []
            while j < len(words) and not (
                words[j] in COMMON_LABEL_STARTS and not looks_like_value_start(words[j])
            ):
                value_words.append(words[j])
                j += 1
            value = " ".join(value_words).strip()
            if label:
                fields[label] = clean_value(value) if value else "TODO"
            i = j
        else:
            i += 1
    return fields


def parse_expected(expected_texts, descriptor_format, descriptor_owner):
    # Cleanup pipeline
    seq = merge_ocr_fragments(expected_texts)
    seq = strip_noise(seq)
    seq = drop_max_fees(seq)
    seq = dedupe_adjacent(seq)

    # Intent: prefer descriptor.intent, fall back to "Review transaction to X".
    intent = (descriptor_format or {}).get("intent") or extract_intent(seq) or "TODO"

    # Remove "Review transaction to X" lines now that intent is extracted.
    seq = [t for t in seq if not _REVIEW_TX_RE.match(t)]

    # Find content after "Interaction with"
    after = seq
    for i, t in enumerate(seq):
        if t.strip() == "Interaction with":
            after = seq[i + 1 :]
            break

    visible_labels = []
    if descriptor_format:
        for f in descriptor_format.get("fields", []) or []:
            if f.get("visible", "always") != "never":
                lbl = f.get("label")
                if lbl:
                    visible_labels.append(lbl)

    # Owner extraction.
    owner = descriptor_owner or "TODO"
    if not descriptor_owner and after:
        owner_candidate, remainder = split_owner_from_first(after[0], visible_labels or None)
        if owner_candidate and len(owner_candidate.split()) <= 4:
            owner = owner_candidate
            if remainder:
                after = [remainder] + after[1:]
            else:
                after = after[1:]

    # Fields extraction.
    fields = {}
    if visible_labels:
        # First try the simple pairwise: each label appears as its own entry, value in next.
        i = 0
        while i < len(after):
            if after[i] in visible_labels:
                lbl = after[i]
                if i + 1 < len(after):
                    fields[lbl] = clean_value(after[i + 1])
                    i += 2
                    continue
            i += 1
        # For any label still missing, try concatenated fallback parse.
        missing = [l for l in visible_labels if l not in fields]
        if missing:
            combined = " ".join(after)
            parsed = parse_label_value_chunks(combined, known_labels=visible_labels)
            for lbl in missing:
                val = parsed.get(lbl, "TODO")
                if val and val != "TODO":
                    fields[lbl] = val
                else:
                    fields[lbl] = "TODO"
    else:
        # No descriptor info at all — purely heuristic. Empty result is fine
        # when the function legitimately has no visible fields.
        combined = " ".join(after)
        fields = parse_label_value_chunks(combined, known_labels=None)

<<<<<<< Updated upstream
=======
    # Strip leading label-name from values — Ledger sometimes duplicates the
    # label across the screen header and the value line (visible in OCR as
    # 'TokenID', 'To', 'kenID 0' → after merge the value entry has the label
    # repeated at its start).
    for lbl in list(fields.keys()):
        v = fields[lbl]
        if isinstance(v, str) and v.startswith(lbl + " "):
            fields[lbl] = v[len(lbl) + 1 :].strip()
        elif isinstance(v, str) and v == lbl:
            fields[lbl] = ""

>>>>>>> Stashed changes
    return {"intent": intent, "owner": owner, "fields": fields}


# ---------------------------------------------------------------------------
# dataProvider extraction
# ---------------------------------------------------------------------------

ENS_RE = re.compile(r"^[A-Za-z0-9_-]+\.eth$")


<<<<<<< Updated upstream
def extract_data_provider(decoded_tx, descriptor_format, parsed_expected):
=======
def _parse_arg_structured(s):
    """Like `_parse_arg` but returns a structured shape that keeps inner
    tuple field names. Tuple shape: {kind: 'tuple', fields: [(shape, name)]}.
    Primitive shape: {kind: 'primitive', type: '<canonical>'}.
    Returns (shape, name)."""
    s = s.strip()
    if not s:
        return ({"kind": "primitive", "type": ""}, None)
    if s.startswith("("):
        depth = 0
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    inner = s[1:i]
                    fields = [_parse_arg_structured(p) for p in _split_top_commas(inner)]
                    rest = s[i + 1 :].strip()
                    arr = ""
                    m = re.match(r"((?:\[\d*\])+)", rest)
                    if m:
                        arr = m.group(1)
                        rest = rest[len(arr) :].strip()
                    return ({"kind": "tuple", "fields": fields, "array": arr}, rest or None)
        return ({"kind": "primitive", "type": s}, None)
    toks = _WS_SPLIT.split(s)
    if len(toks) == 1:
        return ({"kind": "primitive", "type": toks[0]}, None)
    return ({"kind": "primitive", "type": toks[0]}, toks[-1])


def _resolve_path_in_args(path, params_structured, decoded_args):
    """Resolve a dotted path like 'desc.srcToken' or 'srcToken.[-20:]'
    against decoded args. Path parts can be a tuple field name OR a slice
    like '[-20:]' / '[0:20]' to take a sub-range of bytes (used by
    descriptors that store an address inside a longer bytes blob).
    Returns the value or None."""
    parts = [p for p in path.split(".") if p]
    if not parts:
        return None
    # Top-level: find by name
    top = parts[0]
    cur_value = None
    cur_shape = None
    for i, (shape, name) in enumerate(params_structured):
        if name == top:
            cur_value = decoded_args[i]
            cur_shape = shape
            break
    if cur_value is None:
        return None
    for part in parts[1:]:
        # Slice — works on bytes, or on int values that 1inch packs into
        # uint256s for addresses (e.g. `token.[-20:]` on a uint256 arg).
        m = re.fullmatch(r"\[(-?\d+):(-?\d+)?\]", part)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else None
            if isinstance(cur_value, int):
                cur_value = cur_value.to_bytes(32, "big")
            if isinstance(cur_value, (bytes, bytearray)):
                cur_value = bytes(cur_value)[start:end]
                cur_shape = {"kind": "primitive", "type": "bytes"}
                continue
            return None
        # Tuple field by name
        if cur_shape and cur_shape.get("kind") == "tuple":
            for j, (child_shape, child_name) in enumerate(cur_shape["fields"]):
                if child_name == part:
                    cur_value = cur_value[j]
                    cur_shape = child_shape
                    break
            else:
                return None
            continue
        return None
    return cur_value


def _as_address_hex(value):
    """Normalize a decoded address-like value to an EIP-55 checksummed
    0x… string. Accepts Python str (already an address), bytes (length
    20 or 32 with the address in the low 20 bytes), or int — 1inch packs
    addresses into uint256 args so we take the low 160 bits.

    Returning EIP-55 is what the runners produce; if expected values use
    lowercase, the test fails on case alone."""
    raw = None
    if isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
        raw = value
    elif isinstance(value, (bytes, bytearray)):
        b = bytes(value)
        if len(b) >= 20:
            raw = "0x" + b[-20:].hex()
    elif isinstance(value, int):
        raw = "0x" + (value & ((1 << 160) - 1)).to_bytes(20, "big").hex()
    if raw is None:
        return None
    try:
        return to_checksum_address(raw)
    except Exception:
        return raw


def extract_data_provider(decoded_tx, descriptor_format, parsed_expected, fallback_chain_id=1):
>>>>>>> Stashed changes
    """Best-effort dataProvider: for each addressName field, if the parsed
    expected value is an ENS name, add it to addressNames.
    """
    if not descriptor_format:
        return None
    sig = descriptor_format.get("_signature")
    if not sig:
        return None
<<<<<<< Updated upstream
    name, params = parse_signature(sig)
    if not params:
        return None
    types = [t for t, _ in params]
    arg_names = [n for _, n in params]
=======
    _, params_structured = _parse_signature_structured(sig)
    if not params_structured:
        return None
    # Canonical (flat) types for abi_decode
    flat_types = [t for t, _ in parse_signature(sig)[1]]
>>>>>>> Stashed changes
    calldata = decoded_tx["data"]
    if calldata.startswith("0x"):
        calldata = calldata[2:]
    try:
<<<<<<< Updated upstream
        decoded_args = abi_decode(types, bytes.fromhex(calldata[8:]))
    except Exception:
        return None
    args_by_name = {n: v for n, v in zip(arg_names, decoded_args) if n}

    dp_address_names = {}
    dp_tokens = {}
    fields_by_label = parsed_expected.get("fields", {})

=======
        decoded_args = abi_decode(flat_types, bytes.fromhex(calldata[8:]))
    except Exception:
        return None

    chain_id = decoded_tx.get("chainId") or fallback_chain_id
    dp_address_names = {}
    dp_ens_names = {}
    dp_tokens = {}
    fields_by_label = parsed_expected.get("fields", {})

    def _record_token(addr_hex):
        if addr_hex and addr_hex.lower() not in dp_tokens:
            dp_tokens[addr_hex.lower()] = lookup_token_metadata(addr_hex, chain_id)

>>>>>>> Stashed changes
    for field in descriptor_format.get("fields", []) or []:
        if field.get("visible", "always") == "never":
            continue
        fmt = field.get("format")
        label = field.get("label")
        path = field.get("path", "")
<<<<<<< Updated upstream
        if fmt == "addressName":
            addr_value = args_by_name.get(path)
            if addr_value is None:
                continue
            if isinstance(addr_value, bytes):
                addr_hex = "0x" + addr_value.hex()
            else:
                addr_hex = addr_value
            displayed = fields_by_label.get(label, "")
            if isinstance(displayed, str) and ENS_RE.match(displayed):
                dp_address_names[addr_hex.lower()] = displayed
        elif fmt == "tokenAmount":
            params_obj = field.get("params") or {}
            token_path = params_obj.get("tokenPath")
            if not token_path:
                continue
            token_addr = args_by_name.get(token_path)
            if token_addr is None:
                continue
            if isinstance(token_addr, bytes):
                token_hex = "0x" + token_addr.hex()
            else:
                token_hex = token_addr
            dp_tokens[token_hex.lower()] = {
                "symbol": "TODO",
                "decimals": 0,
                "name": "TODO",
            }
=======
        params_obj = field.get("params") or {}

        if fmt == "addressName":
            addr_value = _resolve_path_in_args(path, params_structured, decoded_args)
            addr_hex = _as_address_hex(addr_value)
            if not addr_hex:
                continue
            displayed = fields_by_label.get(label, "")
            # Only emit a name entry when the v1 Ledger output rendered an
            # actual name — not when it just showed the raw 0x address.
            # ENS names go in `ensNames` (kept separate from local contact
            # labels in `addressNames` since descriptor `sources` filters
            # are evaluated against the matching map only).
            if isinstance(displayed, str) and displayed.strip():
                if ENS_RE.match(displayed):
                    dp_ens_names[addr_hex.lower()] = displayed
                elif not re.match(r"^0x[0-9a-fA-F]{40}$", displayed) and displayed not in ("TODO",):
                    dp_address_names[addr_hex.lower()] = displayed
        elif fmt == "tokenAmount":
            token_path = params_obj.get("tokenPath")
            if not token_path:
                continue
            token_addr_val = _resolve_path_in_args(token_path, params_structured, decoded_args)
            token_hex = _as_address_hex(token_addr_val)
            _record_token(token_hex)
>>>>>>> Stashed changes

    dp = {}
    if dp_tokens:
        dp["tokens"] = dp_tokens
    if dp_address_names:
        dp["addressNames"] = dp_address_names
<<<<<<< Updated upstream
    return dp or None


=======
    if dp_ens_names:
        dp["ensNames"] = dp_ens_names
    return dp or None


def _parse_signature_structured(sig_with_names):
    paren = sig_with_names.find("(")
    name = sig_with_names[:paren]
    inside = sig_with_names[paren + 1 : sig_with_names.rfind(")")]
    if not inside.strip():
        return name, []
    return name, [_parse_arg_structured(p) for p in _split_top_commas(inside)]


def _format_token_amount(raw_amount, decimals, symbol):
    """Render a tokenAmount field as the runners do: integer-part + '.' +
    fractional-part trimmed of trailing zeros, followed by ' SYMBOL'."""
    if decimals <= 0:
        return f"{raw_amount} {symbol}"
    s = str(raw_amount).rjust(decimals + 1, "0")
    integer = s[:-decimals].lstrip("0") or "0"
    fractional = s[-decimals:].rstrip("0")
    body = integer if not fractional else f"{integer}.{fractional}"
    return f"{body} {symbol}"


def _resolve_path_in_message(path, message):
    """Resolve a dotted path against an EIP-712 message dict. A leading
    `@.` (some descriptors use this to mean "the contract / typed-data
    container") is stripped — for our purposes the rest of the path is a
    plain field name in the message."""
    if not path:
        return None
    if path.startswith("@."):
        path = path[2:]
    parts = [p for p in path.split(".") if p]
    cur = message
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def extract_data_provider_eip712(data, descriptor_format, parsed_expected, fallback_chain_id=1):
    """EIP-712 counterpart of `extract_data_provider`: walks the message
    dict instead of decoded calldata to populate dataProvider entries for
    every tokenAmount.tokenPath and addressName field."""
    if not descriptor_format or not data:
        return None
    message = data.get("message") or {}
    domain = data.get("domain") or {}
    chain_id = domain.get("chainId") or fallback_chain_id

    dp_address_names = {}
    dp_ens_names = {}
    dp_tokens = {}
    fields_by_label = parsed_expected.get("fields", {})

    def _record_token(addr_hex):
        if addr_hex and addr_hex.lower() not in dp_tokens:
            dp_tokens[addr_hex.lower()] = lookup_token_metadata(addr_hex, chain_id)

    for field in descriptor_format.get("fields", []) or []:
        if field.get("visible", "always") == "never":
            continue
        fmt = field.get("format")
        label = field.get("label")
        path = field.get("path", "")
        params_obj = field.get("params") or {}

        if fmt == "tokenAmount":
            token_path = params_obj.get("tokenPath")
            if token_path:
                token_hex = _as_address_hex(_resolve_path_in_message(token_path, message))
                _record_token(token_hex)
            elif isinstance(params_obj.get("token"), str):
                _record_token(params_obj["token"])
        elif fmt == "addressName":
            addr_value = _resolve_path_in_message(path, message)
            addr_hex = _as_address_hex(addr_value)
            if not addr_hex:
                continue
            displayed = fields_by_label.get(label, "")
            if isinstance(displayed, str) and displayed.strip():
                if ENS_RE.match(displayed):
                    dp_ens_names[addr_hex.lower()] = displayed
                elif not re.match(r"^0x[0-9a-fA-F]{40}$", displayed) and displayed not in ("TODO",):
                    dp_address_names[addr_hex.lower()] = displayed

    dp = {}
    if dp_tokens:
        dp["tokens"] = dp_tokens
    if dp_address_names:
        dp["addressNames"] = dp_address_names
    if dp_ens_names:
        dp["ensNames"] = dp_ens_names
    return dp or None


def fill_expected_from_eip712(expected, data, descriptor_format, dp_tokens):
    """EIP-712 counterpart of `fill_expected_from_decoded`. Replaces
    placeholder values in `expected.fields` for tokenAmount/addressName
    fields using the message data + the resolved token metadata."""
    if not descriptor_format or not data:
        return
    message = data.get("message") or {}
    fields = expected.get("fields") or {}

    def _is_placeholder(v):
        return v in ("TODO", None) or (isinstance(v, str) and ("???" in v or v.strip() == ""))

    for field in descriptor_format.get("fields", []) or []:
        if field.get("visible", "always") == "never":
            continue
        label = field.get("label")
        if not label:
            continue
        current = fields.get(label)
        if not _is_placeholder(current):
            continue
        fmt = field.get("format")
        path = field.get("path", "")
        params_obj = field.get("params") or {}

        if fmt == "tokenAmount":
            amount_val = _resolve_path_in_message(path, message)
            if isinstance(amount_val, str):
                try:
                    amount_val = int(amount_val)
                except ValueError:
                    continue
            token_meta = None
            if params_obj.get("tokenPath"):
                token_addr = _as_address_hex(_resolve_path_in_message(params_obj["tokenPath"], message))
                if token_addr:
                    token_meta = dp_tokens.get(token_addr.lower())
            elif isinstance(params_obj.get("token"), str):
                token_meta = dp_tokens.get(params_obj["token"].lower())
            if isinstance(amount_val, int) and token_meta and token_meta.get("symbol", "TODO") != "TODO":
                fields[label] = _format_token_amount(
                    amount_val, token_meta.get("decimals") or 0, token_meta["symbol"]
                )
        elif fmt == "addressName":
            addr_val = _resolve_path_in_message(path, message)
            addr_hex = _as_address_hex(addr_val)
            if addr_hex:
                fields[label] = addr_hex

    expected["fields"] = fields


def fill_expected_from_decoded(expected, decoded_tx, descriptor_format, dp_tokens):
    """After parse_expected ran on Ledger OCR and dp_tokens was populated
    from rawTx, replace any `???`/`TODO` values for tokenAmount and
    addressName fields with values computed from the decoded args. Only
    overwrites placeholder values; leaves a real OCR-derived value alone.
    """
    if not descriptor_format:
        return
    sig = descriptor_format.get("_signature")
    if not sig:
        return
    _, params_structured = _parse_signature_structured(sig)
    if not params_structured:
        return
    flat_types = [t for t, _ in parse_signature(sig)[1]]
    calldata = decoded_tx["data"]
    if calldata.startswith("0x"):
        calldata = calldata[2:]
    try:
        decoded_args = abi_decode(flat_types, bytes.fromhex(calldata[8:]))
    except Exception:
        return

    fields = expected.get("fields") or {}

    def _is_placeholder(v):
        return v in ("TODO", None) or (isinstance(v, str) and ("???" in v or v.strip() == ""))

    for field in descriptor_format.get("fields", []) or []:
        if field.get("visible", "always") == "never":
            continue
        label = field.get("label")
        if not label:
            continue
        current = fields.get(label)
        if not _is_placeholder(current):
            continue
        fmt = field.get("format")
        path = field.get("path", "")
        params_obj = field.get("params") or {}

        if fmt == "tokenAmount":
            amount_val = _resolve_path_in_args(path, params_structured, decoded_args)
            token_path = params_obj.get("tokenPath")
            token_meta = None
            if token_path:
                token_addr = _as_address_hex(
                    _resolve_path_in_args(token_path, params_structured, decoded_args)
                )
                if token_addr:
                    token_meta = dp_tokens.get(token_addr.lower())
            if isinstance(amount_val, int) and token_meta and token_meta.get("symbol", "TODO") != "TODO":
                fields[label] = _format_token_amount(
                    amount_val, token_meta.get("decimals") or 0, token_meta["symbol"]
                )
        elif fmt == "addressName":
            addr_val = _resolve_path_in_args(path, params_structured, decoded_args)
            addr_hex = _as_address_hex(addr_val)
            if addr_hex:
                # Leave as 0x address; runner may resolve to a name via
                # dataProvider, but the raw hex is the safe fallback.
                fields[label] = addr_hex

    expected["fields"] = fields


>>>>>>> Stashed changes
# ---------------------------------------------------------------------------
# Migration orchestration
# ---------------------------------------------------------------------------

def find_format_calldata(descriptor, calldata_hex):
    if calldata_hex.startswith("0x"):
        calldata_hex = calldata_hex[2:]
    if len(calldata_hex) < 8:
        return None, None
    selector = bytes.fromhex(calldata_hex[:8])
    for sig, fmt in (descriptor.get("display", {}).get("formats", {}) or {}).items():
        try:
            if function_selector(sig) == selector:
                fmt = dict(fmt)
                fmt["_signature"] = sig
                return sig, fmt
        except Exception:
            continue
    return None, None


def find_format_eip712(descriptor, primary_type):
    if not primary_type:
        return None, None
    for sig, fmt in (descriptor.get("display", {}).get("formats", {}) or {}).items():
        if sig == primary_type or sig.startswith(f"{primary_type}("):
            fmt = dict(fmt)
            fmt["_signature"] = sig
            return sig, fmt
    return None, None


def order_keys(t):
    out = {}
    for k in ["description", "rawTx", "data", "txHash", "expected"]:
        if k in t:
            out[k] = t[k]
    return out


def count_todos(expected):
    """Count 'TODO' values in an expected block. Used for reporting."""
    n = 0
    for k in ("intent", "owner"):
        if expected.get(k) == "TODO":
            n += 1
    for v in (expected.get("fields") or {}).values():
        if v == "TODO" or (isinstance(v, dict) and v.get("TODO") == "TODO"):
            n += 1
    return n


<<<<<<< Updated upstream
=======
def _first_deployment_chain_id(descriptor):
    """Pick the first deployment chainId from either context.contract or
    context.eip712 — used as a default when querying Etherscan for static
    token metadata."""
    ctx = descriptor.get("context") or {}
    for key in ("contract", "eip712"):
        deployments = ((ctx.get(key) or {}).get("deployments")) or []
        for dep in deployments:
            cid = (dep or {}).get("chainId")
            if cid:
                return int(cid)
    return None


def _inline_field_refs(descriptor):
    """In-place: resolve any `$ref` on display.formats.*.fields[] entries
    against display.definitions and inline the result.

    Descriptors like 1inch reuse field shapes via
        { "path": "x", "$ref": "$.display.definitions.sendAmount", "params": {...} }
    where `definitions` lives in a `common-*.json` include. Without this
    pass the field looks like it has no label/format and the rest of the
    migration pipeline silently drops it. Local fields override the
    referenced definition; `params` is shallow-merged with local winning.
    """
    formats = (descriptor.get("display") or {}).get("formats") or {}
    for fmt_def in formats.values():
        fields = (fmt_def or {}).get("fields")
        if not isinstance(fields, list):
            continue
        for i, field in enumerate(fields):
            if not isinstance(field, dict):
                continue
            ref = field.get("$ref")
            if not ref:
                continue
            target = _resolve_descriptor_ref(ref, descriptor)
            if not isinstance(target, dict):
                continue
            merged = dict(target)
            merged_params = dict(target.get("params") or {})
            merged_params.update(field.get("params") or {})
            for k, v in field.items():
                if k in ("$ref", "params"):
                    continue
                merged[k] = v
            if merged_params:
                merged["params"] = merged_params
            fields[i] = merged
    return descriptor


>>>>>>> Stashed changes
def load_descriptor_with_includes(descriptor_path, _seen=None):
    """Load a descriptor and recursively merge its `includes`. The including
    file wins on conflicts; `display.formats` and `metadata` are merged.
    """
    _seen = _seen or set()
    p = descriptor_path.resolve()
    if p in _seen:
        return {}
    _seen.add(p)
    with open(p) as f:
        doc = json.load(f)
    includes = doc.get("includes")
    if includes:
        included = load_descriptor_with_includes(p.parent / includes, _seen)
        # Merge: included is the base, doc overrides.
        merged = dict(included)
        for k, v in doc.items():
            if k == "includes":
                continue
            if k == "display" and isinstance(v, dict) and isinstance(merged.get("display"), dict):
                merged_display = dict(merged["display"])
                base_formats = merged_display.get("formats", {}) or {}
                override_formats = (v.get("formats") or {})
                combined = dict(base_formats)
                for sig, fmt in override_formats.items():
                    if sig in combined and isinstance(combined[sig], dict) and isinstance(fmt, dict):
                        merged_fmt = dict(combined[sig])
                        merged_fmt.update(fmt)
                        combined[sig] = merged_fmt
                    else:
                        combined[sig] = fmt
                merged_display["formats"] = combined
                # Carry through other display.* keys
                for dk, dv in v.items():
                    if dk == "formats":
                        continue
                    merged_display[dk] = dv
                merged["display"] = merged_display
            elif k == "metadata" and isinstance(v, dict) and isinstance(merged.get("metadata"), dict):
                merged_meta = dict(merged["metadata"])
                merged_meta.update(v)
                merged["metadata"] = merged_meta
            else:
                merged[k] = v
        return merged
    return doc


<<<<<<< Updated upstream
def migrate_file(tests_v1_path, testsv2_path, descriptor_path):
    with open(tests_v1_path) as f:
        v1 = json.load(f)
    descriptor = load_descriptor_with_includes(descriptor_path)

    owner = descriptor.get("metadata", {}).get("owner")

    dp_tokens, dp_address_names = {}, {}
=======
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def _resolve_descriptor_ref(ref, descriptor):
    """Resolve a `$.path.to.value` reference inside the descriptor."""
    if not isinstance(ref, str) or not ref.startswith("$."):
        return ref
    cur = descriptor
    for part in ref[2:].split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _walk_format_fields(formats):
    for fmt_def in (formats or {}).values():
        for field in (fmt_def or {}).get("fields", []) or []:
            yield field


def audit_data_provider_needs(descriptor):
    """Scan the descriptor for formats that rely on runtime data the runner
    can't synthesize on its own. Returns (static_token_addrs, warnings).

    - `static_token_addrs`: lowercase addresses pulled from `tokenAmount`
      fields whose `params.token` resolves to a literal address (directly or
      via `$.metadata.constants.X`). These should appear in
      `dataProvider.tokens` for the runner to format the amount.

    - `warnings`: human-readable notes about constructs the migration
      script can't auto-fill — token lookups that depend on the tx, unit
      formats whose `base` is a templated constant, addressName fields
      typed as 'token', etc. The caller prints these so the human knows
      which dataProvider entries still need filling in by hand.
    """
    static_token_addrs = set()
    warnings = []
    formats = (descriptor.get("display") or {}).get("formats") or {}

    for field in _walk_format_fields(formats):
        if field.get("visible") == "never":
            continue
        fmt = field.get("format")
        params = field.get("params") or {}
        label = field.get("label") or field.get("path") or "<?>"

        if fmt == "tokenAmount":
            tok = params.get("token")
            if isinstance(tok, str):
                resolved = _resolve_descriptor_ref(tok, descriptor) if tok.startswith("$.") else tok
                if isinstance(resolved, str) and _ADDR_RE.match(resolved):
                    static_token_addrs.add(resolved.lower())
                else:
                    warnings.append(
                        f"tokenAmount field '{label}': params.token={tok!r} "
                        "did not resolve to an address — fill dataProvider.tokens manually"
                    )
            elif params.get("tokenPath"):
                warnings.append(
                    f"tokenAmount field '{label}': uses dynamic tokenPath="
                    f"{params['tokenPath']!r} — add the actual token address(es) "
                    "from the rawTx to dataProvider.tokens"
                )

        elif fmt == "addressName":
            warnings.append(
                f"addressName field '{label}': runner resolves the address "
                "to a display name — if the expected value is a name (e.g. "
                "'USD Coin', 'yohoming.eth'), add an entry to "
                "dataProvider.addressNames"
            )

        elif fmt == "unit":
            base = params.get("base")
            if isinstance(base, str) and base.startswith("$."):
                warnings.append(
                    f"unit field '{label}': base={base!r} is a templated "
                    "constant — runners may not resolve it; verify expected value"
                )

    # Dedupe while keeping order so identical fields across multiple
    # function formats don't double-print.
    seen = set()
    unique_warnings = []
    for w in warnings:
        if w in seen:
            continue
        seen.add(w)
        unique_warnings.append(w)
    return static_token_addrs, unique_warnings


def migrate_file(tests_v1_path, testsv2_path, descriptor_path):
    with open(tests_v1_path) as f:
        v1 = json.load(f)
    descriptor = _inline_field_refs(load_descriptor_with_includes(descriptor_path))

    owner = descriptor.get("metadata", {}).get("owner")

    static_token_addrs, dp_warnings = audit_data_provider_needs(descriptor)
    static_chain_id = _first_deployment_chain_id(descriptor) or 1
    dp_tokens, dp_address_names, dp_ens_names = {}, {}, {}
    for addr in static_token_addrs:
        dp_tokens.setdefault(addr, lookup_token_metadata(addr, static_chain_id))
>>>>>>> Stashed changes
    new_tests = []
    file_todo_total = 0

    for t in v1.get("tests", []):
        new_t = {"description": t.get("description", "TODO")}

        if "rawTx" in t:
            new_t["rawTx"] = t["rawTx"]
            if "txHash" in t:
                new_t["txHash"] = t["txHash"]
            try:
                decoded = decode_signed_tx(t["rawTx"])
                _, fmt = find_format_calldata(descriptor, decoded["data"])
                expected = parse_expected(t.get("expectedTexts", []), fmt, owner)
                new_t["expected"] = expected
<<<<<<< Updated upstream
                dp = extract_data_provider(decoded, fmt, expected)
=======
                dp = extract_data_provider(decoded, fmt, expected, fallback_chain_id=static_chain_id)
>>>>>>> Stashed changes
                if dp:
                    for addr, info in (dp.get("tokens") or {}).items():
                        dp_tokens.setdefault(addr, info)
                    for addr, n in (dp.get("addressNames") or {}).items():
                        dp_address_names.setdefault(addr, n)
<<<<<<< Updated upstream
=======
                    for addr, n in (dp.get("ensNames") or {}).items():
                        dp_ens_names.setdefault(addr, n)
                fill_expected_from_decoded(expected, decoded, fmt, dp_tokens)
>>>>>>> Stashed changes
                file_todo_total += count_todos(expected)
            except Exception as e:
                print(f"      WARN: decode/parse failed for one case: {e}")
                new_t["expected"] = {"intent": "TODO", "owner": owner or "TODO", "fields": {"TODO": "TODO"}}
                file_todo_total += 3
        elif "data" in t:
            new_t["data"] = t["data"]
            if "txHash" in t:
                new_t["txHash"] = t["txHash"]
            primary_type = (t.get("data") or {}).get("primaryType")
            _, fmt = find_format_eip712(descriptor, primary_type)
            expected = parse_expected(t.get("expectedTexts", []), fmt, owner)
            new_t["expected"] = expected
<<<<<<< Updated upstream
=======
            dp = extract_data_provider_eip712(t.get("data"), fmt, expected, fallback_chain_id=static_chain_id)
            if dp:
                for addr, info in (dp.get("tokens") or {}).items():
                    dp_tokens.setdefault(addr, info)
                for addr, n in (dp.get("addressNames") or {}).items():
                    dp_address_names.setdefault(addr, n)
                for addr, n in (dp.get("ensNames") or {}).items():
                    dp_ens_names.setdefault(addr, n)
            fill_expected_from_eip712(expected, t.get("data"), fmt, dp_tokens)
>>>>>>> Stashed changes
            file_todo_total += count_todos(expected)

        new_tests.append(order_keys(new_t))

    relative_descriptor = "../" + descriptor_path.name
    output = {
        "$schema": "../../../specs/erc7730-tests-v2.schema.json",
        "descriptor": relative_descriptor,
    }
    dp = {}
    if dp_tokens:
        dp["tokens"] = dp_tokens
    if dp_address_names:
        dp["addressNames"] = dp_address_names
<<<<<<< Updated upstream
=======
    if dp_ens_names:
        dp["ensNames"] = dp_ens_names
>>>>>>> Stashed changes
    if dp:
        output["dataProvider"] = dp
    output["tests"] = new_tests

    testsv2_path.parent.mkdir(parents=True, exist_ok=True)
    with open(testsv2_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

<<<<<<< Updated upstream
    return file_todo_total
=======
    return file_todo_total, dp_warnings
>>>>>>> Stashed changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity", help="Entity name (process all its tests/ files)")
    ap.add_argument("--file", help="Single tests/ file path")
    ap.add_argument("--registry", default="registry")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if args.file:
        files = [Path(args.file)]
    elif args.entity:
        d = Path(args.registry) / args.entity / "tests"
        if not d.exists():
            print(f"No tests/ folder for entity {args.entity}", file=sys.stderr)
            sys.exit(1)
        files = sorted(d.glob("*.tests.json"))
    else:
        ap.print_help()
        sys.exit(1)

    if not files:
        print("No files to migrate.")
        return

    print(f"Migrating {len(files)} file(s):")
    total_todos = 0
    for path in files:
        entity_root = path.parent.parent
        testsv2_path = entity_root / "testsv2" / path.name
        descriptor_path = entity_root / path.name.replace(".tests.json", ".json")
        if not descriptor_path.exists():
            print(f"  SKIP: {path} — descriptor {descriptor_path} not found")
            continue
        if testsv2_path.exists() and not args.overwrite:
            print(f"  SKIP: {testsv2_path} already exists (use --overwrite)")
            continue
        try:
<<<<<<< Updated upstream
            todos = migrate_file(path, testsv2_path, descriptor_path)
            marker = "" if todos == 0 else f"  ⚠️  {todos} TODO(s)"
            print(f"  {path}{marker}")
=======
            todos, dp_warnings = migrate_file(path, testsv2_path, descriptor_path)
            marker = "" if todos == 0 else f"  ⚠️  {todos} TODO(s)"
            print(f"  {path}{marker}")
            for w in dp_warnings:
                print(f"      dataProvider: {w}")
>>>>>>> Stashed changes
            total_todos += todos
        except Exception:
            print(f"  ERROR migrating {path}:")
            traceback.print_exc()
    if total_todos:
        print(f"\nTotal TODOs to review by hand: {total_todos}")
    else:
        print("\nNo TODOs — clean migration.")


if __name__ == "__main__":
    main()
