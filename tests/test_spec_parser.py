import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "macbook_scraper"))

from utils.spec_parser import SpecParser


@pytest.mark.parametrize("name, expected", [
    ("MacBook Air M4 13 inch 2025 10CPU 8GPU 16GB 256GB", '13"'),
    ("MacBook Air M5 13-inch with 10-core CPU and 8-core GPU 16GB 512GB SSD", '13"'),
    ("MacBook Pro (M5 Pro) 14 inch chip with 15-core CPU", '14"'),
    # CellphoneS writes the size bare after the model type. Previously
    # unparsed, which is what the (now removed) per-product detail-page
    # fetch was compensating for — badly: it appended "13.6es"/"14.2es".
    ("MacBook Pro 14 M5 10CPU 10GPU 24GB 1TB", '14"'),
    ("MacBook Air 15 M3 8GB 256GB", '15"'),
    # Must not mistake RAM or a decimal for a screen size.
    ("MacBook Pro 16GB 512GB", None),
    ("MacBook Air M2 2022 (8GB RAM", None),
])
def test_screen_size(name, expected):
    assert SpecParser().parse(name).get('screen_size') == expected


@pytest.mark.parametrize("name, expected", [
    ("MacBook Air M5 13 inch 2026 10CPU 8GPU 16GB 512GB", 'MacBook Air'),
    ("MacBook Pro (M5 Pro) 14 inch chip with 15-core CPU", 'MacBook Pro'),
    # The chip is "A18 Pro" — a bare "pro" substring check misfiled these.
    ("MacBook Neo 13 inch A18 Pro 2026 6CPU 5GPU 8GB 256GB", 'MacBook Neo'),
    ("Apple MacBook Air M2 2024 8CPU 8GPU 16GB 256GB", 'MacBook Air'),
])
def test_model_type(name, expected):
    assert SpecParser().parse(name)['model_type'] == expected


def test_bare_size_does_not_disturb_other_specs():
    specs = SpecParser().parse("MacBook Pro 14 M5 10CPU 10GPU 24GB 1TB")
    assert (specs['chip'], specs['ram_gb'], specs['storage_display'], specs['cpu_cores']) == ('M5', 24, '1TB', 10)
