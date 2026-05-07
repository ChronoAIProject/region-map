"""Validate config.json structure. Used by test_validate.py and CI."""
import json
import sys
from pathlib import Path


REQUIRED_TOP = ["products", "closure_tiers", "formal_levels",
                "focus_quarter", "archive_rule", "ui"]
REQUIRED_PRODUCT = ["key", "label"]
REQUIRED_CLOSURE = ["key", "label", "color", "trigger"]
REQUIRED_FORMAL = ["key", "shape", "label"]
REQUIRED_LABEL_LANGS = ["en", "zh"]


def _check_label(prefix, label, errors):
    if not isinstance(label, dict):
        errors.append(f"{prefix}.label must be object")
        return
    for lang in REQUIRED_LABEL_LANGS:
        if lang not in label:
            errors.append(f"{prefix}.label.{lang} missing")


def validate_config(cfg):
    errors = []
    for key in REQUIRED_TOP:
        if key not in cfg:
            errors.append(f"top-level key missing: {key}")
            return errors

    for i, p in enumerate(cfg["products"]):
        for k in REQUIRED_PRODUCT:
            if k not in p:
                errors.append(f"products[{i}].{k} missing")
        if "label" in p:
            _check_label(f"products[{i}]", p["label"], errors)

    for i, t in enumerate(cfg["closure_tiers"]):
        for k in REQUIRED_CLOSURE:
            if k not in t:
                errors.append(f"closure_tiers[{i}].{k} missing")
        if "label" in t:
            _check_label(f"closure_tiers[{i}]", t["label"], errors)
        if "trigger" in t:
            _check_label(f"closure_tiers[{i}].trigger", t["trigger"], errors)
        if "color" in t and not (isinstance(t["color"], str) and t["color"].startswith("#")):
            errors.append(f"closure_tiers[{i}].color must be hex string starting with #")

    for i, fl in enumerate(cfg["formal_levels"]):
        for k in REQUIRED_FORMAL:
            if k not in fl:
                errors.append(f"formal_levels[{i}].{k} missing")
        if "label" in fl:
            _check_label(f"formal_levels[{i}]", fl["label"], errors)

    fq = cfg.get("focus_quarter", {})
    for k in ["label", "border_color", "border_width"]:
        if k not in fq:
            errors.append(f"focus_quarter.{k} missing")

    ar = cfg.get("archive_rule", {})
    for k in ["after_mature_days", "opacity"]:
        if k not in ar:
            errors.append(f"archive_rule.{k} missing")

    ui = cfg.get("ui", {})
    if "title" not in ui:
        errors.append("ui.title missing")
    else:
        _check_label("ui.title", ui["title"], errors)
    if "default_lang" not in ui:
        errors.append("ui.default_lang missing")

    return errors


def main():
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        cfg = json.load(f)
    errors = validate_config(cfg)
    if errors:
        print(f"FAIL: {len(errors)} errors in config.json:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: config.json valid ({len(cfg['products'])} products, "
          f"{len(cfg['closure_tiers'])} closure tiers, "
          f"{len(cfg['formal_levels'])} formal levels)")


if __name__ == "__main__":
    main()
