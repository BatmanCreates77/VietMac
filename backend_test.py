#!/usr/bin/env python3
"""
Backend API Tests for VietMac Compare MacBook Pro Price Tracker
Tests the /api/macbook-prices endpoint and related functionality
"""

import requests
import json
import os
from datetime import datetime

# Get base URL from environment
BASE_URL = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://vietmac-compare.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            assert 'status' in data, "Missing 'status' field"
            assert 'timestamp' in data, "Missing 'timestamp' field"
            assert data['status'] == 'healthy', "Status is not 'healthy'"
            
            print("✅ Health endpoint test PASSED")
            return True
        else:
            print(f"❌ Health endpoint test FAILED - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint test FAILED - Error: {str(e)}")
        return False

def test_macbook_prices_endpoint():
    """Test the main MacBook prices endpoint"""
    print("\n=== Testing MacBook Prices Endpoint ===")
    try:
        response = requests.get(f"{API_BASE}/macbook-prices", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure: {list(data.keys())}")
            
            # Validate main response structure
            assert 'success' in data, "Missing 'success' field"
            assert 'prices' in data, "Missing 'prices' field"
            assert 'exchangeRate' in data, "Missing 'exchangeRate' field"
            assert 'timestamp' in data, "Missing 'timestamp' field"
            assert 'source' in data, "Missing 'source' field"
            
            assert data['success'] == True, "Success field is not True"
            assert isinstance(data['prices'], list), "Prices field is not a list"
            assert len(data['prices']) == 4, f"Expected 4 MacBook models, got {len(data['prices'])}"
            
            print(f"✅ Found {len(data['prices'])} MacBook models")
            print(f"✅ Exchange Rate: 1 INR = {data['exchangeRate']} VND")
            print(f"✅ Data Source: {data['source']}")
            
            return data
        else:
            print(f"❌ MacBook prices endpoint test FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ MacBook prices endpoint test FAILED - Error: {str(e)}")
        return None

def test_exchange_rate_validation(data):
    """Test exchange rate validation"""
    print("\n=== Testing Exchange Rate Validation ===")
    try:
        exchange_rate = data['exchangeRate']
        
        # Exchange rate should be a positive number
        assert isinstance(exchange_rate, (int, float)), "Exchange rate is not a number"
        assert exchange_rate > 0, "Exchange rate should be positive"
        
        # Reasonable range for INR to VND (typically 250-350)
        assert 200 <= exchange_rate <= 400, f"Exchange rate {exchange_rate} seems unrealistic"
        
        print(f"✅ Exchange rate validation PASSED: {exchange_rate}")
        return True
        
    except Exception as e:
        print(f"❌ Exchange rate validation FAILED - Error: {str(e)}")
        return False

def test_macbook_models_validation(data):
    """Test MacBook models data structure and content"""
    print("\n=== Testing MacBook Models Validation ===")
    
    expected_models = [
        {'id': 'm3-max-36-1tb', 'config': 'M3 Max, 36GB RAM, 1TB SSD'},
        {'id': 'm4-pro-24-512gb', 'config': 'M4 Pro, 24GB RAM, 512GB SSD'},
        {'id': 'm4-max-36-1tb', 'config': 'M4 Max, 36GB RAM, 1TB SSD'},
        {'id': 'm4-max-48-1tb', 'config': 'M4 Max, 48GB RAM, 1TB SSD'}
    ]
    
    try:
        prices = data['prices']
        found_models = []
        
        for item in prices:
            print(f"\nValidating model: {item.get('id', 'Unknown')}")
            
            # Required fields validation
            required_fields = ['model', 'configuration', 'id', 'vndPrice', 'available', 
                             'inrPrice', 'vatRefund', 'finalPrice']
            
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"
            
            # Data type validation
            assert isinstance(item['model'], str), "Model should be string"
            assert isinstance(item['configuration'], str), "Configuration should be string"
            assert isinstance(item['id'], str), "ID should be string"
            assert isinstance(item['available'], bool), "Available should be boolean"
            
            # Price validation (can be None for unavailable items)
            if item['vndPrice'] is not None:
                assert isinstance(item['vndPrice'], (int, float)), "VND price should be number"
                assert item['vndPrice'] > 0, "VND price should be positive"
                
                assert isinstance(item['inrPrice'], (int, float)), "INR price should be number"
                assert item['inrPrice'] > 0, "INR price should be positive"
                
                assert isinstance(item['vatRefund'], (int, float)), "VAT refund should be number"
                assert item['vatRefund'] > 0, "VAT refund should be positive"
                
                assert isinstance(item['finalPrice'], (int, float)), "Final price should be number"
                assert item['finalPrice'] > 0, "Final price should be positive"
            
            found_models.append(item['id'])
            print(f"✅ Model {item['id']} validation PASSED")
        
        # Check if all expected models are present
        for expected in expected_models:
            assert expected['id'] in found_models, f"Missing expected model: {expected['id']}"
        
        print(f"✅ All {len(expected_models)} expected MacBook models found and validated")
        return True
        
    except Exception as e:
        print(f"❌ MacBook models validation FAILED - Error: {str(e)}")
        return False

def test_price_calculations(data):
    """Test price calculation accuracy"""
    print("\n=== Testing Price Calculations ===")
    
    try:
        exchange_rate = data['exchangeRate']
        prices = data['prices']
        
        for item in prices:
            if item['vndPrice'] is not None:
                print(f"\nTesting calculations for {item['id']}:")
                
                # Calculate expected values
                expected_inr = item['vndPrice'] / exchange_rate
                expected_vat = expected_inr * 0.085  # 8.5% VAT refund
                expected_final = expected_inr - expected_vat
                
                # Allow for rounding differences
                inr_diff = abs(item['inrPrice'] - round(expected_inr))
                vat_diff = abs(item['vatRefund'] - round(expected_vat))
                final_diff = abs(item['finalPrice'] - round(expected_final))
                
                print(f"  VND Price: {item['vndPrice']:,}")
                print(f"  Expected INR: {round(expected_inr):,}, Actual: {item['inrPrice']:,}, Diff: {inr_diff}")
                print(f"  Expected VAT: {round(expected_vat):,}, Actual: {item['vatRefund']:,}, Diff: {vat_diff}")
                print(f"  Expected Final: {round(expected_final):,}, Actual: {item['finalPrice']:,}, Diff: {final_diff}")
                
                assert inr_diff <= 1, f"INR calculation error too large: {inr_diff}"
                assert vat_diff <= 1, f"VAT calculation error too large: {vat_diff}"
                assert final_diff <= 1, f"Final price calculation error too large: {final_diff}"
                
                # Verify VAT refund is approximately 8.5% of INR price
                vat_percentage = (item['vatRefund'] / item['inrPrice']) * 100
                assert 8.4 <= vat_percentage <= 8.6, f"VAT percentage {vat_percentage:.2f}% not around 8.5%"
                
                print(f"✅ Calculations for {item['id']} are accurate")
        
        print("✅ All price calculations validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Price calculations validation FAILED - Error: {str(e)}")
        return False

def test_error_handling():
    """Test API error handling for invalid endpoints"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test invalid endpoint
        response = requests.get(f"{API_BASE}/invalid-endpoint", timeout=10)
        print(f"Invalid endpoint status: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            assert 'error' in data, "Missing error field in 404 response"
            print("✅ 404 error handling works correctly")
        else:
            print(f"⚠️  Expected 404, got {response.status_code}")
        
        # Test POST method (should return 405)
        response = requests.post(f"{API_BASE}/macbook-prices", timeout=10)
        print(f"POST method status: {response.status_code}")
        
        if response.status_code == 405:
            data = response.json()
            assert 'error' in data, "Missing error field in 405 response"
            print("✅ Method not allowed handling works correctly")
        else:
            print(f"⚠️  Expected 405, got {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test FAILED - Error: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting VietMac Compare Backend API Tests")
    print(f"Testing API at: {API_BASE}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        'health_endpoint': False,
        'macbook_prices_endpoint': False,
        'exchange_rate_validation': False,
        'macbook_models_validation': False,
        'price_calculations': False,
        'error_handling': False
    }
    
    # Test health endpoint
    results['health_endpoint'] = test_health_endpoint()
    
    # Test main MacBook prices endpoint
    price_data = test_macbook_prices_endpoint()
    if price_data:
        results['macbook_prices_endpoint'] = True
        
        # Run validation tests on the data
        results['exchange_rate_validation'] = test_exchange_rate_validation(price_data)
        results['macbook_models_validation'] = test_macbook_models_validation(price_data)
        results['price_calculations'] = test_price_calculations(price_data)
    
    # Test error handling
    results['error_handling'] = test_error_handling()
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Backend needs attention.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)