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


# Names as the shops list them (2026-10-01): CellphoneS, ShopDunk, FPTShop.
@pytest.mark.parametrize("name, model_type, chip, variant", [
    ("Apple Mac mini M6 12CPU 12GPU 16GB 256GB 2026", 'Mac mini', 'M6', None),
    ("Mac mini M6 12CPU/12GPU/16GB/256GB", 'Mac mini', 'M6', None),
    # "Pro" belongs to the chip; this is not a MacBook Pro.
    ("Mac mini M5 Pro chip with 15-core CPU and 16-core GPU, 24GB, 512GB SSD", 'Mac mini', 'M5', 'Pro'),
    ("Mac mini M2 (10-Core GPU| 8GB RAM | 256GB SSD)", 'Mac mini', 'M2', None),
    ("iMac M4 2024 24 inch 8CPU 8GPU 16GB 256GB", 'iMac', 'M4', None),
    ("iMac 24 inch M4 2024 10CPU/10GPU/16GB/256GB", 'iMac', 'M4', None),
    ("Apple Mac Studio M5 Max 18CPU 32GPU 36GB 512GB 2026", 'Mac Studio', 'M5', 'Max'),
    ("Mac Studio M5 Ultra 30CPU/64GPU/96GB/1TB", 'Mac Studio', 'M5', 'Ultra'),
    ("MacBook Neo 13 inch A18 Pro 2026 6CPU 5GPU 8GB 256GB", 'MacBook Neo', 'A18', 'Pro'),
    ("Macbook Air M5 13-inch with 10‑core CPU and 10‑core GPU 16GB", 'MacBook Air', 'M5', None),
])
def test_mac_lines_and_chips(name, model_type, chip, variant):
    specs = SpecParser().parse(name)
    assert (specs['model_type'], specs['chip'], specs['chip_variant']) == (model_type, chip, variant)


def test_desktop_specs_and_id():
    specs = SpecParser().parse("Mac Studio M5 Ultra chip with 30-core CPU, 64-core GPU, 96GB, 1TB")
    assert (specs['cpu_cores'], specs['gpu_cores'], specs['ram_gb'], specs['storage_display']) == (30, 64, 96, '1TB')
    assert specs['screen_size'] is None
    assert specs['id'] == 'm5-ultra-studio-96-1tb'
    assert SpecParser().parse("iMac M4 2024 24 inch 8CPU 8GPU 16GB 256GB")['screen_size'] == '24"'


@pytest.mark.parametrize("name, model_type, storage", [
    ("iPhone 18 Pro Max 256GB", 'iPhone 18 Pro Max', '256GB'),
    ("iPhone 17 Pro 256GB | Chính hãng", 'iPhone 17 Pro', '256GB'),
    ("Điện thoại iPhone 16 Pro Max 256GB", 'iPhone 16 Pro Max', '256GB'),
    ("iPhone 17e 512 GB", 'iPhone 17e', '512GB'),
    ("iPhone 16e 128GB | Chính hãng VN/A", 'iPhone 16e', '128GB'),
    ("iPhone Air 1TB", 'iPhone Air', '1TB'),
    ("iPhone Duo 2TB", 'iPhone Duo', '2TB'),
    ("iPhone 16 Plus 128GB", 'iPhone 16 Plus', '128GB'),
    ("iPhone 13 mini 128GB", 'iPhone 13 mini', '128GB'),
    ("iPhone 18 Pro 256GB Đen MJRP4X/A", 'iPhone 18 Pro', '256GB'),
])
def test_iphone_model_and_storage(name, model_type, storage):
    specs = SpecParser().parse_iphone(name)
    assert (specs['model_type'], specs['storage_display']) == (model_type, storage)
    assert specs['chip'] is None and specs['screen_size'] is None


def test_iphone_id_and_storage_gb():
    specs = SpecParser().parse_iphone("iPhone 17 Pro Max 2TB")
    assert (specs['id'], specs['storage_gb'], specs['generation']) == ('iphone-17-pro-max-2tb', 2048, 17)
