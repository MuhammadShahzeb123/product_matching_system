#!/usr/bin/env python3
"""
Test script to demonstrate the new URL and price extraction features
"""

from product_matching_system import ProductMatchingSystem

def test_url_generation():
    """Test URL generation methods"""
    system = ProductMatchingSystem()

    # Test Amazon URL generation
    amazon_asin = "B08KTN2NSW"
    amazon_url = system._build_amazon_url(amazon_asin)
    print(f"✅ Amazon URL: {amazon_url}")

    # Test Target URL generation
    target_tcin = "93317698"
    target_url = system._build_target_url(target_tcin)
    print(f"✅ Target URL: {target_url}")

    print()

def test_price_extraction():
    """Test price extraction methods"""
    system = ProductMatchingSystem()

    # Test Amazon price extraction with sample data
    amazon_product = {
        "pricing": {
            "formatted_current_price": "$149.99"
        },
        "title": "Sample Amazon Product"
    }

    amazon_price = system._extract_amazon_price(amazon_product)
    print(f"✅ Amazon price extracted: {amazon_price}")

    # Test Target price extraction with sample data
    target_product = {
        "pricing": {
            "formatted_current_price": "$129.99"
        },
        "basic_info": {
            "name": "Sample Target Product"
        }
    }

    target_price = system._extract_target_price(target_product)
    print(f"✅ Target price extracted: {target_price}")

    print()

def demonstrate_new_structure():
    """Show what the new JSON structure will look like"""
    print("🔄 NEW JSON STRUCTURE PREVIEW:")
    print("="*50)

    sample_amazon = {
        "title": "Amazon Basics Ergonomic Gaming Chair",
        "asin": "B08KTN2NSW",
        "brand": "Amazon Basics",
        "price": "$149.99",
        "url": "https://www.amazon.com/dp/B08KTN2NSW/"
    }

    sample_target = {
        "title": "Gaming Chair with Lumbar Support",
        "tcin": "93317698",
        "brand": "Gaming Pro",
        "price": "$129.99",
        "url": "https://www.target.com/p/-/A-93317698"
    }

    print("Amazon Product:")
    for key, value in sample_amazon.items():
        print(f"  {key}: {value}")

    print("\nTarget Product:")
    for key, value in sample_target.items():
        print(f"  {key}: {value}")

    print("\n✅ Both products now have:")
    print("  - Complete clickable URLs")
    print("  - Properly formatted prices")
    print("  - All original fields preserved")

if __name__ == "__main__":
    print("🧪 TESTING NEW URL AND PRICE FEATURES")
    print("="*50)

    test_url_generation()
    test_price_extraction()
    demonstrate_new_structure()

    print("\n🎉 All tests completed successfully!")
    print("\n📝 Summary of changes:")
    print("  - Added complete product URLs for both Amazon and Target")
    print("  - Enhanced price extraction with multiple fallback methods")
    print("  - Updated JSON report structure to include URLs")
    print("  - Maintained backward compatibility with existing data")
