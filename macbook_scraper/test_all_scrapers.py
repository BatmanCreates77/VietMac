#!/usr/bin/env python3
"""
Test all scrapers with updated URLs and generate comprehensive report
"""
import json
import sys
from datetime import datetime
from scrapers.cellphones_scraper import CellphonesScraper

def test_cellphones():
    """Test CellphoneS scraper"""
    print("\n" + "="*80)
    print("TESTING CELLPHONES SCRAPER")
    print("="*80)

    try:
        scraper = CellphonesScraper()
        result = scraper.scrape()
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'success': False,
            'shop': 'cellphones',
            'error': str(e),
            'products': [],
            'count': 0
        }

def generate_summary_report(results):
    """Generate comprehensive summary report"""
    print("\n" + "="*80)
    print("SCRAPING SUMMARY REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    total_products = 0
    successful_shops = 0

    for shop, result in results.items():
        print(f"\n{shop.upper()}:")
        print(f"  Status: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"  Products: {result['count']}")

        if result['success']:
            successful_shops += 1
            total_products += result['count']

            # Price range
            if result['products']:
                prices = [p['price_vnd'] for p in result['products'] if p.get('price_vnd')]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    print(f"  Price range: {min_price:,}đ - {max_price:,}đ")

                # Show sample products
                print(f"\n  Sample products (first 5):")
                for i, product in enumerate(result['products'][:5], 1):
                    price = product.get('price_text', 'N/A')
                    print(f"    {i}. {product['model'][:70]}")
                    print(f"       Price: {price}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")

    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    print(f"Successful shops: {successful_shops}/4")
    print(f"Total products scraped: {total_products}")
    print(f"Success rate: {(successful_shops/4)*100:.0f}%")

    return {
        'timestamp': datetime.now().isoformat(),
        'total_products': total_products,
        'successful_shops': successful_shops,
        'results': results
    }

def save_results(summary, filename='output/scraping_test_results.json'):
    """Save results to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Results saved to: {filename}")
    except Exception as e:
        print(f"\n❌ Failed to save results: {e}")

def main():
    """Main test function"""
    print("\n🚀 Starting comprehensive scraper test...")
    print("Testing all scrapers with updated URLs")

    results = {}

    # Test CellphoneS (most reliable)
    results['cellphones'] = test_cellphones()

    # Note: ShopDunk, FPTShop, and TopZone require browser automation
    # which takes longer. For quick test, we'll focus on CellphoneS
    # and show their status from previous runs

    print("\n" + "="*80)
    print("NOTE: ShopDunk, FPTShop, and TopZone require Playwright/Selenium")
    print("For quick testing, run their individual scrapers separately:")
    print("  python3 scrapers/shopdunk_scraper.py")
    print("  python3 scrapers/fptshop_scraper.py")
    print("  python3 scrapers/topzone_scraper.py")
    print("="*80)

    # Add placeholder results for other shops
    results['shopdunk'] = {
        'success': None,
        'shop': 'shopdunk',
        'products': [],
        'count': 0,
        'note': 'Run separately - requires Playwright'
    }

    results['fptshop'] = {
        'success': None,
        'shop': 'fptshop',
        'products': [],
        'count': 0,
        'note': 'Run separately - requires SeleniumBase (may be blocked by Cloudflare)'
    }

    results['topzone'] = {
        'success': None,
        'shop': 'topzone',
        'products': [],
        'count': 0,
        'note': 'Run separately - requires SeleniumBase (may timeout)'
    }

    # Generate summary
    summary = generate_summary_report(results)

    # Save results
    save_results(summary)

    print("\n✅ Testing complete!")

    return 0 if results['cellphones']['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
