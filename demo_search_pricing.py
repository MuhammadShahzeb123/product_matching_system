#!/usr/bin/env python3
"""
Demo: Amazon Search-Based Pricing Extraction
Demonstrates the exact pricing format requested by the user
"""

from amazon_complete_fetcher_parser import AmazonProductExtractor

def demo_search_pricing():
    """Demonstrate search-based pricing extraction"""
    print("🎯 Amazon Search-Based Pricing Demo")
    print("=" * 50)
    
    # Test with gaming chair that has price variations
    test_asin = "B0DTK7VDTH"
    
    # Initialize with search-based pricing enabled (default)
    extractor = AmazonProductExtractor(use_search_pricing=True)
    
    print(f"🛒 Extracting product: {test_asin}")
    print("📈 Search-based pricing: ENABLED")
    print("-" * 50)
    
    try:
        result = extractor.extract_product(test_asin)
        
        if result:
            print("✅ SEARCH-BASED PRICING EXTRACTED!")
            print()
            
            # Get pricing data
            pricing = result.get('pricing', {})
            search_enhancement = result.get('search_enhancement', {})
            marketplace_data = result.get('marketplace_data', {})
            
            # Your requested format examples:
            search_current = pricing.get('search_current_price', pricing.get('formatted_current_price', ''))
            search_list = pricing.get('search_list_price', pricing.get('list_price', ''))
            more_choices = pricing.get('more_buying_choices', {})
            more_choices_text = more_choices.get('text', '') if isinstance(more_choices, dict) else more_choices
            
            print("💰 EXACT FORMAT YOU REQUESTED:")
            print("-" * 30)
            
            # Format 1: "$109.99 List: $179.99"
            if search_current and search_list:
                print(f"💲 {search_current} List: {search_list}")
            
            # Format 2: "More Buying Choices $107.79(2+ used & new offers)"
            if more_choices_text:
                print(f"🛒 More Buying Choices {more_choices_text}")
            
            print()
            print("📊 COMPARISON WITH DETAIL PAGE:")
            print("-" * 30)
            detail_price = pricing.get('current_price', 'N/A')
            print(f"📄 Detail Page Price: {detail_price}")
            print(f"🔍 Search Current Price: {search_current}")
            
            if search_current and detail_price and detail_price != 'N/A':
                try:
                    search_val = float(search_current.replace('$', '').replace(',', ''))
                    detail_val = float(detail_price.replace('$', '').replace(',', ''))
                    savings = detail_val - search_val
                    print(f"💡 Search shows ${savings:.2f} {'LOWER' if savings > 0 else 'HIGHER'} price!")
                except:
                    pass
                    
            print()
            print("🏪 SELLER INFORMATION FROM SEARCH:")
            print("-" * 30)
            seller_info = result.get('seller_info', {})
            fulfillment_info = result.get('fulfillment_info', {})
            
            primary_seller = seller_info.get('primary_seller', 'N/A')
            fulfillment = fulfillment_info.get('fulfillment_type', 'N/A')
            ships_from = seller_info.get('sold_by', 'N/A')
            
            print(f"🏪 Seller: {primary_seller}")
            print(f"📦 Fulfillment: {fulfillment}")
            print(f"🚚 Ships from: {ships_from}")
            
            # Show enhancement details
            if search_enhancement.get('pricing_enhanced'):
                print(f"✅ Pricing enhanced from search results")
            if search_enhancement.get('seller_enhanced'):
                print(f"✅ Seller info enhanced from search results")
                
        else:
            print("❌ Search enhancement data not available")
            print("ℹ️  This can happen due to network issues or Amazon's anti-bot measures")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")

if __name__ == "__main__":
    demo_search_pricing()
