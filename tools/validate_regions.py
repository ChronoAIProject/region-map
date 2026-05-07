"""Validate regions.json against config.json. Used by test_validate.py and CI."""
import json
import sys
from pathlib import Path


REQUIRED_REGION = ["label", "desc", "closure", "formal", "product",
                   "milestone", "owner", "issue_count", "focus",
                   "archived", "promoted_at", "deps"]


def validate_regions(regions_doc, cfg):
    errors = []
    if "regions" not in regions_doc:
        errors.append("regions key missing at top level")
        return errors

    regions = regions_doc["regions"]
    valid_closures = {t["key"] for t in cfg.get("closure_tiers", [])}
    valid_formals = {f["key"] for f in cfg.get("formal_levels", [])}
    valid_products = {p["key"] for p in cfg.get("products", [])}
    region_keys = set(regions.keys())

    for rid, r in regions.items():
        for k in REQUIRED_REGION:
            if k not in r:
                errors.append(f"region '{rid}'.{k} missing")
        if r.get("closure") not in valid_closures and "closure" in r:
            errors.append(
                f"region '{rid}'.closure='{r['closure']}' not in config.closure_tiers")
        if r.get("formal") not in valid_formals and "formal" in r:
            errors.append(
                f"region '{rid}'.formal='{r['formal']}' not in config.formal_levels")
        if r.get("product") not in valid_products and "product" in r:
            errors.append(
                f"region '{rid}'.product='{r['product']}' not in config.products")
        for dep in (r.get("deps") or []):
            dep_key = dep if isinstance(dep, str) else dep.get("key")
            if dep_key == rid:
                errors.append(f"region '{rid}' has self-dep")
            elif dep_key not in region_keys:
                errors.append(f"region '{rid}' dep '{dep_key}' is unknown")
        if "label" in r:
            for lang in ("en", "zh"):
                if lang not in r["label"]:
                    errors.append(f"region '{rid}'.label.{lang} missing")

    return errors


def main():
    repo_root = Path(__file__).parent.parent
    with open(repo_root / "config.json") as f:
        cfg = json.load(f)
    with open(repo_root / "regions.json") as f:
        regions_doc = json.load(f)
    errors = validate_regions(regions_doc, cfg)
    if errors:
        print(f"FAIL: {len(errors)} errors in regions.json:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    n = len(regions_doc["regions"])
    print(f"OK: regions.json valid ({n} regions)")


if __name__ == "__main__":
    main()
