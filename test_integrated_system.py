#!/usr/bin/env python3
"""
Test the integrated Amazon system with search-based pricing extraction
"""

import sys
import json
from amazon_complete_fetcher_parser import AmazonProductExtractor

def test_gaming_chair_with_search_pricing():
    """Test gaming chair extraction with search-based pricing"""
    print("🧪 Testing Integrated Amazon System with Search-Based Pricing")
    print("=" * 60)
    
    # Use a specific gaming chair product ASIN/URL instead of search
    gaming_chair_asin = "B0DTK7VDTH"  # Use existing product from workspace
    
    # Initialize with search-based pricing enabled
    extractor = AmazonProductExtractor(use_search_pricing=True)
    
    try:
        print(f"🎯 Testing product ASIN: {gaming_chair_asin}")
        print("📈 Using search-based pricing extraction...")
        
        # Extract with search-based pricing
        result = extractor.extract_product(gaming_chair_asin)
        
        if result:
            print("\n✅ EXTRACTION SUCCESSFUL!")
            print("📊 Raw data structure preview:")
            print(f"   - Product Keys: {list(result.keys())}")
            
            # Check for search-enhanced pricing
            if 'search_enhancement' in result:
                search_data = result['search_enhancement']
                print(f"   - Search Enhancement Keys: {list(search_data.keys())}")
                
                # Show the pricing comparison
                print("\n💰 PRICING COMPARISON:")
                detail_price = result.get('pricing', {}).get('price')
                search_price = search_data.get('current_price')
                list_price = search_data.get('list_price')
                more_choices = search_data.get('more_buying_choices')
                
                print(f"   📄 Detail Page Price: {detail_price}")
                print(f"   🔍 Search Current Price: {search_price}")
                print(f"   🏷️  Search List Price: {list_price}")
                print(f"   🛒 More Buying Choices: {more_choices}")
                
                if search_price and detail_price:
                    try:
                        search_val = float(search_price.replace('$', '').replace(',', ''))
                        detail_val = float(detail_price.replace('$', '').replace(',', ''))
                        difference = detail_val - search_val
                        print(f"   💡 Price Difference: ${difference:.2f} (Search is {'lower' if difference > 0 else 'higher'})")
                    except:
                        pass
            
            # Save result
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_integrated_gaming_chair_{timestamp}.json"
            filepath = f"c:\\Users\\zarya\\Desktop\\Python\\product_matching_system\\{filename}"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
            
            return True
        else:
            print("❌ No product data extracted")
            return False
            
    except Exception as e:
        print(f"💥 Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_product_with_pricing():
    """Test specific product URL with pricing"""
    print("\n" + "=" * 60)
    print("🧪 Testing Specific Product with Search Enhancement")
    print("=" * 60)
    
    # Test with a specific product that might have pricing issues
    product_asin = "B0DTK7VDTH"
    
    extractor = AmazonProductExtractor(use_search_pricing=True)
    
    try:
        print(f"🎯 Testing product ASIN: {product_asin}")
        print("📈 Search pricing enhancement: ENABLED")
        
        result = extractor.extract_product(product_asin)
        
        if result:
            print("\n✅ EXTRACTION SUCCESSFUL!")
            
            # Focus on pricing data
            print("\n💰 PRICING ANALYSIS:")
            detail_price = result.get('pricing', {}).get('price')
            
            if 'search_enhancement' in result:
                search_data = result['search_enhancement']
                print(f"   🔍 Search Current Price: {search_data.get('current_price', 'N/A')}")
                print(f"   🔍 Search List Price: {search_data.get('list_price', 'N/A')}")
                print(f"   🔍 Search Coupon: {search_data.get('coupon_info', 'N/A')}")
                print(f"   🔍 More Buying Choices: {search_data.get('more_buying_choices', 'N/A')}")
                print(f"   🔍 Search Seller: {search_data.get('seller_name', 'N/A')}")
                print(f"   🔍 Fulfillment Type: {search_data.get('fulfillment_type', 'N/A')}")
            
            # Compare with detail page pricing
            print(f"   📄 Detail Page Price: {detail_price}")
            
            # Show the exact format you requested
            if 'search_enhancement' in result:
                search_data = result['search_enhancement']
                current = search_data.get('current_price', '')
                list_p = search_data.get('list_price', '')
                choices = search_data.get('more_buying_choices', '')
                
                print(f"\n🎯 YOUR REQUESTED FORMAT:")
                if current and list_p:
                    print(f"   💰 {current} List: {list_p}")
                if choices:
                    print(f"   🛒 More Buying Choices {choices}")
            
            return True
        else:
            print("❌ No product data extracted")
            return False
            
    except Exception as e:
        print(f"💥 Error during extraction: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Integrated System Test")
    print("Testing search-based pricing enhancement...")
    
    # Test 1: Search query with pricing
    success1 = test_gaming_chair_with_search_pricing()
    
    # Test 2: Specific product with enhancement
    success2 = test_specific_product_with_pricing()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"🔍 Search Query Test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"🎯 Product URL Test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 or success2:
        print("\n🎉 Integration successful! Search-based pricing is working.")
    else:
        print("\n⚠️ Integration issues detected. Check the logs above.")
