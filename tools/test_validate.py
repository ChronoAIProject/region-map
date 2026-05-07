"""Tests for region-map validators. Run with: python3 -m unittest test_validate.py"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from validate_config import validate_config  # noqa: E402


class TestValidateConfig(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "_meta": {"version": 1},
            "products": [
                {"key": "nyxid", "label": {"en": "NyxID", "zh": "NyxID"}}
            ],
            "closure_tiers": [
                {
                    "key": "seed",
                    "label": {"en": "Proposed", "zh": "提出"},
                    "color": "#bdc3c7",
                    "trigger": {"en": "...", "zh": "..."}
                }
            ],
            "formal_levels": [
                {"key": "none", "shape": "ellipse",
                 "label": {"en": "No auto", "zh": "无"}}
            ],
            "focus_quarter": {
                "label": {"en": "Focus", "zh": "焦点"},
                "border_color": "#c0392b",
                "border_width": 3
            },
            "archive_rule": {"after_mature_days": 30, "opacity": 0.35},
            "ui": {"title": {"en": "T", "zh": "T"}, "default_lang": "zh"}
        }

    def test_valid_config_passes(self):
        errors = validate_config(self.valid_config)
        self.assertEqual(errors, [])

    def test_missing_products_fails(self):
        cfg = dict(self.valid_config)
        del cfg["products"]
        errors = validate_config(cfg)
        self.assertTrue(any("products" in e for e in errors))

    def test_closure_tier_missing_color_fails(self):
        cfg = json.loads(json.dumps(self.valid_config))
        del cfg["closure_tiers"][0]["color"]
        errors = validate_config(cfg)
        self.assertTrue(any("color" in e for e in errors))

    def test_formal_level_missing_shape_fails(self):
        cfg = json.loads(json.dumps(self.valid_config))
        del cfg["formal_levels"][0]["shape"]
        errors = validate_config(cfg)
        self.assertTrue(any("shape" in e for e in errors))

    def test_real_config_passes(self):
        repo_root = HERE.parent
        with open(repo_root / "config.json") as f:
            cfg = json.load(f)
        errors = validate_config(cfg)
        self.assertEqual(errors, [], f"Real config.json has errors: {errors}")


from validate_regions import validate_regions  # noqa: E402


class TestValidateRegions(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "products": [{"key": "nyxid", "label": {"en": "N", "zh": "N"}}],
            "closure_tiers": [{"key": "seed", "label": {"en": "P", "zh": "提"},
                              "color": "#aaa", "trigger": {"en": "x", "zh": "x"}}],
            "formal_levels": [{"key": "none", "shape": "ellipse",
                              "label": {"en": "N", "zh": "无"}}],
        }
        self.valid_regions = {
            "_meta": {"version": 1},
            "regions": {
                "NyxID-A": {
                    "label": {"en": "A", "zh": "A"},
                    "desc": {"en": "x", "zh": "x"},
                    "closure": "seed",
                    "formal": "none",
                    "product": "nyxid",
                    "milestone": "M0",
                    "owner": "kaiweijw",
                    "issue_count": 3,
                    "focus": True,
                    "archived": False,
                    "promoted_at": {},
                    "deps": []
                }
            }
        }

    def test_valid_regions_pass(self):
        errors = validate_regions(self.valid_regions, self.valid_config)
        self.assertEqual(errors, [])

    def test_unknown_closure_fails(self):
        regions = json.loads(json.dumps(self.valid_regions))
        regions["regions"]["NyxID-A"]["closure"] = "nonexistent"
        errors = validate_regions(regions, self.valid_config)
        self.assertTrue(any("closure" in e and "nonexistent" in e for e in errors))

    def test_unknown_product_fails(self):
        regions = json.loads(json.dumps(self.valid_regions))
        regions["regions"]["NyxID-A"]["product"] = "ghostproduct"
        errors = validate_regions(regions, self.valid_config)
        self.assertTrue(any("product" in e and "ghostproduct" in e for e in errors))

    def test_unknown_formal_fails(self):
        regions = json.loads(json.dumps(self.valid_regions))
        regions["regions"]["NyxID-A"]["formal"] = "ghostformal"
        errors = validate_regions(regions, self.valid_config)
        self.assertTrue(any("formal" in e and "ghostformal" in e for e in errors))

    def test_dangling_dep_fails(self):
        regions = json.loads(json.dumps(self.valid_regions))
        regions["regions"]["NyxID-A"]["deps"] = ["NyxID-DoesNotExist"]
        errors = validate_regions(regions, self.valid_config)
        self.assertTrue(any("dep" in e.lower() and "NyxID-DoesNotExist" in e for e in errors))

    def test_self_dep_fails(self):
        regions = json.loads(json.dumps(self.valid_regions))
        regions["regions"]["NyxID-A"]["deps"] = ["NyxID-A"]
        errors = validate_regions(regions, self.valid_config)
        self.assertTrue(any("self" in e.lower() for e in errors))

    def test_real_regions_passes(self):
        repo_root = HERE.parent
        with open(repo_root / "config.json") as f:
            cfg = json.load(f)
        with open(repo_root / "regions.json") as f:
            regions = json.load(f)
        errors = validate_regions(regions, cfg)
        self.assertEqual(errors, [], f"Real regions.json errors: {errors}")


if __name__ == "__main__":
    unittest.main()
