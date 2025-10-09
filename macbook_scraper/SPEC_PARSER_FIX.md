# Spec Parser Integration - Fix Summary

## Problem
The scrapers were collecting prices from all shops, but model and config information was missing or blank for CellphoneS and ShopDunk products. The data only had basic fields like `model`, `price`, `url`, but no structured specs like chip type, RAM, storage, CPU/GPU cores, etc.

## Root Cause
The `SpecParser` utility existed in `/macbook_scraper/utils/spec_parser.py` but was not being used by any of the scrapers. Each scraper was only extracting basic product information without parsing the detailed specifications from product names.

## Solution Implemented

### 1. Integrated SpecParser into All Scrapers
Updated all four scrapers to import and use the `SpecParser`:
- ✅ `cellphones_scraper.py`
- ✅ `shopdunk_scraper.py`
- ✅ `fptshop_scraper.py`
- ✅ `topzone_scraper.py`

Each scraper now:
1. Initializes a `SpecParser` instance in `__init__()`
2. Parses product names using `self.spec_parser.parse(raw_name)`
3. Adds structured `specs` object to each product

### 2. Enhanced Storage Parsing
Fixed the spec parser to handle multiple storage format patterns:
- **With SSD keyword**: "512GB SSD", "1TB SSD"
- **Without SSD keyword**: "16GB 512GB" (CellphoneS format)

The parser now:
- First tries to match patterns with "SSD" keyword
- Falls back to finding all GB/TB mentions and uses the last one as storage
- Correctly distinguishes RAM from storage when both use GB

### 3. Product Data Structure
Each product now includes:

```json
{
  "model": "MacBook Pro 14 inch M4 2024",
  "raw_name": "MacBook Pro 14 inch M4 2024 (16GB RAM| 10 core GPU| 10 core CPU| 512GB SSD)",
  "price_vnd": 37590000,
  "price_text": "37.590.000₫",
  "url": "https://shopdunk.com/...",
  "shop": "shopdunk",
  "specs": {
    "model_type": "MacBook Pro",
    "chip": "M4",
    "chip_variant": null,
    "screen_size": "14\"",
    "cpu_cores": 10,
    "gpu_cores": 10,
    "ram_gb": 16,
    "storage_gb": 512,
    "storage_display": "512GB",
    "year": 2024
  },
  "product_id": "m4-pro-14-16-512gb",
  "clean_name": "MacBook Pro 14\" M4 10C 10G 16GB 512GB"
}
```

## Verification

### ShopDunk (Working Perfectly)
- ✅ All specs parsed correctly
- ✅ 44 products scraped successfully
- ✅ Example: MacBook Pro 14" M4 with full specs (chip, RAM, storage, CPU/GPU cores)

### CellphoneS (Needs Additional Fix)
- ⚠️ Currently returning 0 products
- **Issue**: Website now uses JavaScript to load products dynamically
- **Solution needed**: Update to use Playwright instead of requests+BeautifulSoup
- The spec parser integration is complete and will work once products are scraped

## Files Modified
1. `/macbook_scraper/utils/spec_parser.py` - Enhanced storage parsing
2. `/macbook_scraper/scrapers/cellphones_scraper.py` - Added spec parser integration
3. `/macbook_scraper/scrapers/shopdunk_scraper.py` - Added spec parser integration
4. `/macbook_scraper/scrapers/fptshop_scraper.py` - Added spec parser integration
5. `/macbook_scraper/scrapers/topzone_scraper.py` - Added spec parser integration

## Next Steps
1. Update CellphoneS scraper to use Playwright for JavaScript rendering
2. Test with live scraping to ensure all shops return complete specs
3. Update API transformation logic if needed to use new structured specs

## Testing
Run the spec parser test:
```bash
cd macbook_scraper
python utils/spec_parser.py
```

Run full scraper:
```bash
cd macbook_scraper
python update_prices.py
```

Check output:
```bash
cat output/latest_products.json
```
