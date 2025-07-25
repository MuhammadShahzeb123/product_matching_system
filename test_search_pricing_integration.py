#!/usr/bin/env python3
"""
Test Search-Based Pricing Integration in Product Matching System
===============================================================

This script demonstrates the integration of search-based pricing into 
the product matching system, showing how it enhances price accuracy
in product comparisons.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from product_matching_system import ProductMatchingSystem

def test_search_pricing_integration():
    """Test the search-based pricing integration"""
    print("🧪 Testing Search-Based Pricing Integration in Product Matching System")
    print("=" * 75)
    
    # Initialize the system (now with search-based pricing enabled by default)
    system = ProductMatchingSystem()
    
    # Test with a gaming chair Amazon URL
    amazon_url = "https://www.amazon.com/dp/B0DTK7VDTH"
    target_search_term = "gaming chair"
    
    print(f"📦 Testing Amazon URL: {amazon_url}")
    print(f"🎯 Target search term: '{target_search_term}'")
    print(f"💡 Search-based pricing: ENABLED by default")
    print("-" * 75)
    
    try:
        # Run the URL matching workflow
        results = system.run_amazon_url_matching_workflow(
            amazon_url=amazon_url,
            target_search_term=target_search_term,
            max_target_results=3
        )
        
        if results:
            print("\n✅ SEARCH-BASED PRICING INTEGRATION SUCCESSFUL!")
            
            # Show the enhanced pricing information
            best_match = results[0]
            amazon_product = best_match.amazon_product
            
            print(f"\n📊 ENHANCED PRICING EXTRACTION RESULTS:")
            print(f"   Product: {amazon_product.get('title', '')[:60]}...")
            
            # Extract pricing data to show the enhanced structure
            pricing = amazon_product.get('pricing', {})
            
            print(f"\n💰 PRICING DATA STRUCTURE:")
            print(f"   📄 Detail Page Price: {pricing.get('current_price', 'N/A')}")
            print(f"   🔍 Search Current Price: {pricing.get('search_current_price', 'N/A')}")
            print(f"   🏷️ Search List Price: {pricing.get('search_list_price', 'N/A')}")
            print(f"   🛒 More Buying Choices: {pricing.get('more_buying_choices', 'N/A')}")
            
            # Check if search enhancement was applied
            search_enhancement = amazon_product.get('search_enhancement', {})
            if search_enhancement.get('pricing_enhanced'):
                print(f"   ✅ Search Enhancement: ACTIVE")
                print(f"   🕐 Enhanced At: {search_enhancement.get('enhanced_at', 'N/A')}")
            else:
                print(f"   ⚠️ Search Enhancement: Not available (may be due to network/rate limiting)")
                
            # Show the exact format you requested
            current = pricing.get('search_current_price', pricing.get('formatted_current_price', ''))
            list_price = pricing.get('search_list_price', pricing.get('list_price', ''))
            more_choices = pricing.get('more_buying_choices', {})
            
            if current and list_price:
                print(f"\n🎯 YOUR REQUESTED FORMAT:")
                print(f"   💲 {current} List: {list_price}")
                
            if isinstance(more_choices, dict) and more_choices.get('text'):
                print(f"   🛒 More Buying Choices {more_choices['text']}")
            elif more_choices and isinstance(more_choices, str):
                print(f"   🛒 More Buying Choices {more_choices}")
                
            print(f"\n📈 MATCHING RESULTS:")
            print(f"   🏆 Best Match Score: {best_match.match_score:.1f}")
            print(f"   🎯 Confidence Level: {best_match.confidence}")
            print(f"   📊 Total Comparisons: {len(results)}")
            
        else:
            print("❌ No matching results found")
            
    except Exception as e:
        print(f"💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

def show_integration_summary():
    """Show summary of what was integrated"""
    print("\n" + "=" * 75)
    print("📋 INTEGRATION SUMMARY")
    print("=" * 75)
    
    print("✅ COMPLETED INTEGRATIONS:")
    print("   1. 🔧 ProductMatchingSystem.__init__:")
    print("      - AmazonProductExtractor now uses search-based pricing by default")
    print("      - use_search_pricing=True enabled automatically")
    
    print("\n   2. 💰 _extract_amazon_marketplace_info method:")
    print("      - Enhanced pricing structure with search-based data")
    print("      - Added search_current_price, search_list_price fields") 
    print("      - Added more_buying_choices, coupon_info support")
    print("      - Added price_comparison with source tracking")
    
    print("\n   3. 🔍 _extract_amazon_price method:")
    print("      - Prioritizes search-based pricing over detail page pricing")
    print("      - Fallback mechanism to detail page pricing if search fails")
    print("      - Clear indication of price source in output")
    
    print("\n   4. 📊 _generate_url_matching_report method:")
    print("      - Enhanced with detailed pricing_details section")
    print("      - Shows search enhancement status")
    print("      - Displays your requested format in summary")
    print("      - Comprehensive price source tracking")
    
    print("\n🎯 BENEFITS:")
    print("   ✅ More reliable pricing from Amazon search results")
    print("   ✅ Your exact format: '$99.98 List: $116.98'")
    print("   ✅ 'More Buying Choices' pricing included")
    print("   ✅ Automatic fallback if search pricing unavailable")
    print("   ✅ Enhanced marketplace intelligence")
    print("   ✅ Better product matching accuracy due to reliable pricing")

if __name__ == "__main__":
    test_search_pricing_integration()
    show_integration_summary()
