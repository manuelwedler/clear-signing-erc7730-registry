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
import re
import sys
import traceback
from pathlib import Path

from eth_utils import keccak
from eth_abi import decode as abi_decode
import rlp


# ---------------------------------------------------------------------------
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
        return {
            "chainId": None,
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
    """Combine ['R', 'eview…'] → ['Review…']."""
    out, i = [], 0
    while i < len(texts):
        if (
            i + 1 < len(texts)
            and len(texts[i]) == 1
            and texts[i].isalpha()
            and texts[i].isupper()
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
    # Walk: collect a run of digit-only tokens following an initial decimal number.
    if not re.fullmatch(r"\d+\.\d+", parts[0]):
        return v
    merged = parts[0]
    i = 1
    while i < len(parts) and parts[i].isdigit():
        merged += parts[i]
        i += 1
    return " ".join([merged] + parts[i:])


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

    return {"intent": intent, "owner": owner, "fields": fields}


# ---------------------------------------------------------------------------
# dataProvider extraction
# ---------------------------------------------------------------------------

ENS_RE = re.compile(r"^[A-Za-z0-9_-]+\.eth$")


def extract_data_provider(decoded_tx, descriptor_format, parsed_expected):
    """Best-effort dataProvider: for each addressName field, if the parsed
    expected value is an ENS name, add it to addressNames.
    """
    if not descriptor_format:
        return None
    sig = descriptor_format.get("_signature")
    if not sig:
        return None
    name, params = parse_signature(sig)
    if not params:
        return None
    types = [t for t, _ in params]
    arg_names = [n for _, n in params]
    calldata = decoded_tx["data"]
    if calldata.startswith("0x"):
        calldata = calldata[2:]
    try:
        decoded_args = abi_decode(types, bytes.fromhex(calldata[8:]))
    except Exception:
        return None
    args_by_name = {n: v for n, v in zip(arg_names, decoded_args) if n}

    dp_address_names = {}
    dp_tokens = {}
    fields_by_label = parsed_expected.get("fields", {})

    for field in descriptor_format.get("fields", []) or []:
        if field.get("visible", "always") == "never":
            continue
        fmt = field.get("format")
        label = field.get("label")
        path = field.get("path", "")
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

    dp = {}
    if dp_tokens:
        dp["tokens"] = dp_tokens
    if dp_address_names:
        dp["addressNames"] = dp_address_names
    return dp or None


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


def migrate_file(tests_v1_path, testsv2_path, descriptor_path):
    with open(tests_v1_path) as f:
        v1 = json.load(f)
    descriptor = load_descriptor_with_includes(descriptor_path)

    owner = descriptor.get("metadata", {}).get("owner")

    dp_tokens, dp_address_names = {}, {}
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
                dp = extract_data_provider(decoded, fmt, expected)
                if dp:
                    for addr, info in (dp.get("tokens") or {}).items():
                        dp_tokens.setdefault(addr, info)
                    for addr, n in (dp.get("addressNames") or {}).items():
                        dp_address_names.setdefault(addr, n)
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
    if dp:
        output["dataProvider"] = dp
    output["tests"] = new_tests

    testsv2_path.parent.mkdir(parents=True, exist_ok=True)
    with open(testsv2_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    return file_todo_total


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
            todos = migrate_file(path, testsv2_path, descriptor_path)
            marker = "" if todos == 0 else f"  ⚠️  {todos} TODO(s)"
            print(f"  {path}{marker}")
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
