"""
Text processing utilities for the "less text, better segmentation" experiment.

QaTa-COV19 captions are a single string of three comma-separated sentences:
    1. nature     : "Unilateral/Bilateral pulmonary infection"
    2. quantity   : "one~four infected area(s)"
    3. location   : "<verticals> <left|right> lung [and ...]"  (spatial zones)

This module parses those attributes with plain regular expressions (no extra
NLP dependency), builds reduced text variants used as supervision signals, and
provides an analysis helper for statistics (token length / coverage / noise).

All functions are pure and do NOT touch the original training pipeline.
"""

import re
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Zone definitions (6 lung zones: Upper/Middle/Lower x Left/Right)
# ---------------------------------------------------------------------------
ZONES: List[str] = ["UL", "ML", "LL", "UR", "MR", "LR"]
ZONE_INDEX: Dict[str, int] = {z: i for i, z in enumerate(ZONES)}
_SIDE_PREFIX = {"left": "L", "right": "R"}
_VERTICALS = ("upper", "middle", "lower")

# Supported text modes for build_variant()
MODES = ("full", "nature", "quantity", "location", "keyword",
         "kw_nature", "kw_quantity", "kw_location")

# Reverse map: quantity int -> number word (for single-keyword variants)
_QUANTITY_WORDS = {1: "one", 2: "two", 3: "three", 4: "four"}

# ---------------------------------------------------------------------------
# Regexes (all case-insensitive, robust to spacing issues)
# ---------------------------------------------------------------------------
_NATURE_RE = re.compile(r"\b(unilateral|bilateral)\b", re.IGNORECASE)

_QUANTITY_RE = re.compile(r"\b(one|two|three|four)\s+infected", re.IGNORECASE)
_QUANTITY_MAP = {"one": 1, "two": 2, "three": 3, "four": 4}

# One spatial region, e.g.:
#   "all left lung"                          -> all verticals of left lung
#   "upper middle lower left lung"           -> UL, ML, LL
#   "middle lower right lung"                -> MR, LR
#   "lower left lung"                        -> LL
_REGION_RE = re.compile(
    r"(?:(?P<all>all)\s+"
    r"|(?P<vert>(?:upper|middle|lower)(?:\s+(?:upper|middle|lower))*)\s+)?"
    r"(?P<side>left|right)\s+lung",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _parse_nature(caption: str) -> (Optional[int], bool):
    """Return (0 for unilateral / 1 for bilateral, is_ok)."""
    m = _NATURE_RE.search(caption)
    if m is None:
        return None, False
    return 0 if m.group(1).lower() == "unilateral" else 1, True


def _parse_quantity(caption: str) -> (Optional[int], bool):
    """Return (1..4, is_ok)."""
    m = _QUANTITY_RE.search(caption)
    if m is None:
        return None, False
    return _QUANTITY_MAP[m.group(1).lower()], True


def _parse_location(caption: str) -> (List[str], int, str):
    """Return (zones, num_regions, canonical_location_text)."""
    matches = list(_REGION_RE.finditer(caption))
    if not matches:
        return [], 0, ""

    zones: List[str] = []
    for m in matches:
        side_prefix = _SIDE_PREFIX[m.group("side").lower()]
        if m.group("all") is not None or m.group("vert") is None:
            # "all X lung" or bare "X lung" -> every vertical of that side
            for v in ("U", "M", "L"):
                zones.append(v + side_prefix)
        else:
            for v in m.group("vert").lower().split():
                zones.append(v[0].upper() + side_prefix)

    # de-duplicate while preserving order
    seen, uniq = set(), []
    for z in zones:
        if z not in seen:
            seen.add(z)
            uniq.append(z)

    # canonical location text (reconstructed from matched regions)
    loc_text = " and ".join(m.group(0).strip() for m in matches)
    return uniq, len(matches), loc_text


def parse_caption(caption: str) -> Dict:
    """Parse a full caption into structured attributes.

    Returns dict with keys:
      raw, nature (0/1), nature_ok, quantity (1-4), quantity_ok,
      locations (list of zones), location_ok, num_regions, location_text,
      nature_text, quantity_text.
    """
    nature, nature_ok = _parse_nature(caption)
    quantity, quantity_ok = _parse_quantity(caption)
    locations, num_regions, loc_text = _parse_location(caption)

    nature_text = f"{'bilateral' if nature == 1 else 'unilateral'} pulmonary infection"
    quantity_text = f"{quantity} infected area(s)"

    return {
        "raw": caption,
        "nature": nature,
        "nature_ok": nature_ok,
        "quantity": quantity,
        "quantity_ok": quantity_ok,
        "locations": locations,
        "location_ok": len(locations) > 0,
        "num_regions": num_regions,
        "location_text": loc_text,
        "nature_text": nature_text if nature_ok else "",
        "quantity_text": quantity_text if quantity_ok else "",
    }


# ---------------------------------------------------------------------------
# Variant building
# ---------------------------------------------------------------------------
def build_variant(parsed: Dict, mode: str = "full") -> str:
    """Build a reduced text variant for the given mode.

    mode:
      full        -> original caption (baseline)
      nature      -> first sentence only   ("bilateral pulmonary infection")
      quantity    -> second sentence only  ("2 infected area(s)")
      location    -> third sentence only   ("all left lung and middle lower right lung.")
      keyword     -> compact structured    ("bilateral, 2, all left lung and middle lower right lung.")
      kw_nature   -> single nature keyword ("bilateral")
      kw_quantity -> single quantity keyword ("two")
      kw_location -> single location keyword ("lower right lung")

    Falls back to the raw caption if the requested attribute is not parseable.
    """
    if mode == "full":
        return parsed["raw"]

    nature_s = "bilateral" if parsed["nature"] == 1 else (
        "unilateral" if parsed["nature"] == 0 else None)
    quantity_s = str(parsed["quantity"]) if parsed["quantity_ok"] else None
    loc_s = (parsed["location_text"] + ".") if parsed["location_ok"] else None

    if mode == "nature":
        return f"{nature_s} pulmonary infection" if nature_s else parsed["raw"]
    if mode == "quantity":
        return f"{quantity_s} infected area(s)" if quantity_s else parsed["raw"]
    if mode == "location":
        return loc_s if loc_s else parsed["raw"]
    if mode == "keyword":
        parts = [p for p in (nature_s, quantity_s, loc_s) if p]
        return ", ".join(parts) if parts else parsed["raw"]

    # ---- single-keyword modes ----
    if mode == "kw_nature":
        return nature_s if nature_s else parsed["raw"]
    if mode == "kw_quantity":
        qw = _QUANTITY_WORDS.get(parsed["quantity"]) if parsed["quantity_ok"] else None
        return qw if qw else parsed["raw"]
    if mode == "kw_location":
        return parsed["location_text"] if parsed["location_ok"] else parsed["raw"]

    raise ValueError(f"Unknown mode: {mode!r}. Supported: {MODES}")


def to_labels(parsed: Dict) -> Dict:
    """Convert parsed attributes into supervision labels for aux heads.

    Returns dict with:
      nature        : 0/1 or None
      nature_ok     : bool
      quantity      : 0..3 (class index) or None   [quantity-1 for 4 classes]
      quantity_ok   : bool
      location      : list[float] length 6 (multi-hot)
      location_ok   : bool
    """
    loc = [0.0] * 6
    for z in parsed["locations"]:
        if z in ZONE_INDEX:
            loc[ZONE_INDEX[z]] = 1.0

    return {
        "nature": parsed["nature"],
        "nature_ok": parsed["nature_ok"],
        "quantity": (parsed["quantity"] - 1) if parsed["quantity_ok"] else None,
        "quantity_ok": parsed["quantity_ok"],
        "location": loc,
        "location_ok": parsed["location_ok"],
    }


def process_caption(caption: str, mode: str = "full") -> str:
    """Convenience: parse + build variant in one call."""
    return build_variant(parse_caption(caption), mode)


# ---------------------------------------------------------------------------
# Analysis helpers (coverage / noise statistics)
# ---------------------------------------------------------------------------
def analyze_captions(captions: List[str]) -> Dict:
    """Aggregate parse statistics over a list of captions."""
    n = len(captions)
    stats = {
        "total": n,
        "nature_ok": 0,
        "quantity_ok": 0,
        "location_ok": 0,
        "all_ok": 0,
        "quantity_region_mismatch": 0,   # quantity != num_regions
        "max_tokens": 0,
        "unmatched": [],
    }
    for cap in captions:
        p = parse_caption(cap)
        stats["nature_ok"] += int(p["nature_ok"])
        stats["quantity_ok"] += int(p["quantity_ok"])
        stats["location_ok"] += int(p["location_ok"])
        stats["all_ok"] += int(p["nature_ok"] and p["quantity_ok"] and p["location_ok"])
        if p["quantity_ok"] and p["num_regions"] and p["quantity"] != p["num_regions"]:
            stats["quantity_region_mismatch"] += 1
        # rough token count (whitespace split, like CXR-BERT approx)
        stats["max_tokens"] = max(stats["max_tokens"], len(cap.split()))
        if not (p["nature_ok"] and p["quantity_ok"] and p["location_ok"]):
            stats["unmatched"].append(cap)
    return stats


def summarize_csv(csv_path: str) -> Dict:
    """Analyze all captions in a CSV (Image,Description) file."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    captions = [str(c) for c in df["Description"].tolist()]
    return analyze_captions(captions)


# ---------------------------------------------------------------------------
# CLI self-test: python utils/text_process.py <csv_path>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    paths = sys.argv[1:] or [
        "data/QaTa-COV19-v2/prompt/train.csv",
        "data/QaTa-COV19-v2/prompt/test.csv",
    ]
    for path in paths:
        print(f"\n===== {path} =====")
        s = summarize_csv(path)
        for k, v in s.items():
            if k != "unmatched":
                print(f"  {k}: {v}")
        if s["unmatched"]:
            print(f"  # unmatched: {len(s['unmatched'])} (shown below)")
            for u in s["unmatched"][:15]:
                print(f"    !! {u}")
