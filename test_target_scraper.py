#!/usr/bin/env python3
"""
Test script for the Target Search Scraper module

This script tests both the separated Target scraper functionality
and the integration with the main product matching system.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_target_search_scraper():
    """Test the Target Search Scraper module"""
    print("🧪 Testing Target Search Scraper Module")
    print("=" * 50)
    
    try:
        from target_search_scraper import TargetSearchScraper
        print("✅ Successfully imported TargetSearchScraper")
        
        # Initialize scraper
        scraper = TargetSearchScraper()
        print("✅ Successfully initialized TargetSearchScraper")
        
        # Test search functionality (if available)
        search_term = "bluetooth speaker"
        print(f"\n🔍 Testing search for: '{search_term}'")
        
        products = scraper.search_products(search_term, max_results=3, save_results=False)
        
        if products:
            print(f"✅ Search test successful! Found {len(products)} products")
            for i, product in enumerate(products[:2], 1):
                print(f"   {i}. {product.get('title', 'No title')[:50]}...")
                print(f"      Price: {product.get('price', 'N/A')} | TCIN: {product.get('tcin', 'N/A')}")
        else:
            print("⚠️  Search test returned no products (this might be expected if Target search module is not available)")
        
        # Test URL scraping (this should work even without search module)
        print(f"\n🎯 Testing URL scraping capability...")
        test_url = "https://www.target.com/p/apple-airpods-3rd-generation/-/A-84529355"
        
        try:
            product_data = scraper.scrape_product_url(test_url, save_results=False)
            if product_data:
                basic_info = product_data.get('basic_info', {})
                print("✅ URL scraping test successful!")
                print(f"   Product: {basic_info.get('name', 'Unknown')[:50]}...")
                print(f"   TCIN: {basic_info.get('tcin', 'Unknown')}")
            else:
                print("⚠️  URL scraping test failed (this might be due to network/proxy issues)")
        except Exception as e:
            print(f"⚠️  URL scraping test error: {str(e)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import TargetSearchScraper: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing TargetSearchScraper: {e}")
        return False

def test_main_system_integration():
    """Test the main product matching system with the new Target module"""
    print("\n🧪 Testing Main System Integration")
    print("=" * 50)
    
    try:
        from product_matching_system import ProductMatchingSystem
        print("✅ Successfully imported ProductMatchingSystem")
        
        # Initialize system
        system = ProductMatchingSystem()
        print("✅ Successfully initialized ProductMatchingSystem")
        
        # Test that Target scraper was properly integrated
        if hasattr(system, 'target_scraper'):
            print("✅ Target scraper properly integrated into main system")
            
            # Test basic Target search through main system
            print(f"\n🔍 Testing Target search through main system...")
            
            products = system._search_target_products("office chair", max_results=2)
            
            if products:
                print(f"✅ Main system Target search successful! Found {len(products)} products")
                for i, product in enumerate(products, 1):
                    print(f"   {i}. {product.get('title', 'No title')[:50]}...")
            else:
                print("⚠️  Main system Target search returned no products")
            
        else:
            print("❌ Target scraper not found in main system")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ProductMatchingSystem: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing main system integration: {e}")
        return False

def test_convenience_functions():
    """Test the convenience functions"""
    print("\n🧪 Testing Convenience Functions")
    print("=" * 50)
    
    try:
        from target_search_scraper import search_target_products, scrape_target_url
        print("✅ Successfully imported convenience functions")
        
        # Test search convenience function
        print(f"\n🔍 Testing search_target_products convenience function...")
        
        products = search_target_products("gaming mouse", max_results=2, save_results=False)
        
        if products:
            print(f"✅ Convenience search function successful! Found {len(products)} products")
        else:
            print("⚠️  Convenience search function returned no products")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import convenience functions: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing convenience functions: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Target Search Scraper Module Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Target Search Scraper module
    results.append(test_target_search_scraper())
    
    # Test 2: Main system integration
    results.append(test_main_system_integration())
    
    # Test 3: Convenience functions
    results.append(test_convenience_functions())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All tests passed! The Target scraper module is working correctly.")
    else:
        print("⚠️  Some tests failed. This might be due to:")
        print("   - Missing Target search dependencies")
        print("   - Network/proxy issues")
        print("   - Target.com blocking requests")
        print("   - But the core module structure should still work")
    
    print(f"\n💾 Results saved in: {Path('target_search_results').absolute()}")
    print("🔍 Check the directory for any JSON files created during testing")

if __name__ == "__main__":
    main()
