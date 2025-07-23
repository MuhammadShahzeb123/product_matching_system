#!/usr/bin/env python3
"""
Test script to demonstrate the new intelligent Target search feature
"""

import json
from product_matching_system import ProductMatchingSystem

def test_intelligent_search():
    """Test the intelligent Target search using sample Amazon product data"""
    
    # Load the sample Amazon product data
    with open('amazon_product_B00FS3VJAO_1753271184.json', 'r', encoding='utf-8') as f:
        amazon_product = json.load(f)
    
    print("🧪 TESTING INTELLIGENT TARGET SEARCH")
    print("="*60)
    
    # Show the Amazon product we're working with
    print(f"📦 Amazon Product: {amazon_product['title'][:80]}...")
    print(f"🏷️  Brand: {amazon_product['brand']}")
    print(f"💰 Price: {amazon_product['pricing']['current_price']}")
    print(f"📏 Dimensions: {amazon_product['specifications']['Product Dimensions']}")
    print(f"🔢 UPC: {amazon_product['specifications']['UPC']}")
    
    # Initialize the system
    system = ProductMatchingSystem()
    
    # Test the search query generation
    print(f"\n🔍 GENERATING INTELLIGENT SEARCH QUERIES:")
    print("-"*50)
    
    search_queries = system._create_intelligent_target_search_query(
        amazon_product, 
        "office chair"
    )
    
    print(f"\n📋 Generated {len(search_queries)} search strategies:")
    for i, query in enumerate(search_queries, 1):
        print(f"   {i}. '{query}'")
    
    # Test the intelligent search
    print(f"\n🎯 TESTING INTELLIGENT SEARCH:")
    print("-"*50)
    
    target_products = system._search_target_products_intelligently(
        amazon_product,
        "office chair", 
        max_results=3
    )
    
    if target_products:
        print(f"\n✅ SUCCESS! Found {len(target_products)} Target products")
        print(f"\n📊 MATCHING PREVIEW:")
        print("-"*50)
        
        for i, product in enumerate(target_products, 1):
            name = product.get('basic_info', {}).get('name', 'Unknown')
            brand = product.get('basic_info', {}).get('brand', 'Unknown')
            tcin = product.get('basic_info', {}).get('tcin', 'Unknown')
            print(f"{i}. {name[:60]}...")
            print(f"   Brand: {brand} | TCIN: {tcin}")
            print()
    else:
        print("❌ No products found")
    
    print("🎉 Intelligent search test completed!")

def demonstrate_improvement():
    """Show the improvement over generic search"""
    print(f"\n💡 IMPROVEMENT DEMONSTRATION:")
    print("="*60)
    
    print("🔴 OLD METHOD:")
    print("   - Generic search: 'gaming chair'")
    print("   - Results: Random chairs, not necessarily matching")
    print("   - Match scores: Low (like 105 for unrelated products)")
    
    print(f"\n🟢 NEW INTELLIGENT METHOD:")
    print("   - UPC search: '848837002053' (exact product match)")
    print("   - Brand + Dimensions: 'office chair BestOffice 19.7 x 18.9 x 38 inch'")
    print("   - Brand search: 'office chair BestOffice'")
    print("   - Results: Much more relevant products")
    print("   - Match scores: Higher and more meaningful")
    
    print(f"\n🎯 EXPECTED BENEFITS:")
    print("   ✅ Higher precision matches")
    print("   ✅ Better use of Amazon product data")
    print("   ✅ UPC searches give exact matches when available")
    print("   ✅ Fallback strategies ensure we still find products")
    print("   ✅ More meaningful match scores")

if __name__ == "__main__":
    try:
        test_intelligent_search()
        demonstrate_improvement()
    except FileNotFoundError:
        print("❌ Amazon product JSON file not found")
        print("💡 Make sure 'amazon_product_B00FS3VJAO_1753271184.json' is in the current directory")
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
