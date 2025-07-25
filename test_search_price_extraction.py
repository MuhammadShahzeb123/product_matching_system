#!/usr/bin/env python3
"""
Test Amazon Search Price Extraction

This script tests extracting price information from Amazon search results
to get current price, list price, more buying choices, and seller info.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

# Import scraping dependencies
try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

from bs4 import BeautifulSoup
from urllib.parse import quote_plus


class AmazonSearchPriceExtractor:
    """Extract price and seller info from Amazon search results"""
    
    def __init__(self):
        self.setup_scraping_config()
    
    def setup_scraping_config(self):
        """Setup scraping configuration"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Default proxy
        self.proxies = {
            "http": "http://250621Ev04e-resi_region-US_California:5PjDM1IoS0JSr2c@ca.proxy-jet.io:1010",
            "https": "http://250621Ev04e-resi_region-US_California:5PjDM1IoS0JSr2c@ca.proxy-jet.io:1010"
        }
        
        self.timeout = 30
    
    def search_and_extract_prices(self, search_term: str, max_results: int = 10) -> Dict:
        """Search Amazon and extract price info from search results"""
        
        print(f"🔍 Searching Amazon for: '{search_term}'")
        print(f"📊 Max results: {max_results}")
        
        # Step 1: Get search results
        html_content = self._get_search_results(search_term)
        if not html_content:
            return {'error': 'Failed to get search results'}
        
        # Step 2: Parse and extract product data
        products = self._parse_search_results(html_content, max_results)
        
        # Step 3: Create result
        result = {
            'search_term': search_term,
            'timestamp': datetime.now().isoformat(),
            'products_found': len(products),
            'products': products
        }
        
        return result
    
    def _get_search_results(self, search_term: str) -> Optional[str]:
        """Get search results HTML"""
        try:
            encoded_term = quote_plus(search_term)
            url = f"https://www.amazon.com/s?k={encoded_term}"
            
            print(f"🌐 Fetching: {url}")
            
            if CURL_CFFI_AVAILABLE:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    impersonate="chrome120",
                    timeout=self.timeout
                )
            else:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                print(f"✅ Successfully fetched search results ({len(response.text)} chars)")
                return response.text
            else:
                print(f"❌ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching search results: {e}")
            return None
    
    def _parse_search_results(self, html_content: str, max_results: int) -> List[Dict]:
        """Parse search results and extract product price data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find product containers
            product_containers = soup.find_all('div', {
                'data-component-type': 's-search-result'
            })
            
            print(f"🔍 Found {len(product_containers)} product containers")
            
            products = []
            for i, container in enumerate(product_containers[:max_results]):
                try:
                    product_data = self._extract_product_price_data(container)
                    if product_data:
                        products.append(product_data)
                        print(f"  ✓ Product {i+1}: {product_data.get('title', 'N/A')[:50]}...")
                    else:
                        print(f"  ⚠ Product {i+1}: No valid data extracted")
                        
                except Exception as e:
                    print(f"  ❌ Product {i+1}: Error - {e}")
                    continue
            
            print(f"📊 Successfully extracted {len(products)} products")
            return products
            
        except Exception as e:
            print(f"❌ Error parsing search results: {e}")
            return []
    
    def _extract_product_price_data(self, container) -> Optional[Dict]:
        """Extract price and seller data from search result container"""
        try:
            product = {}
            
            # Basic info
            product['asin'] = container.get('data-asin', '')
            
            # Title
            title_element = container.find('h2', class_='a-size-mini') or container.find('span', class_='a-size-medium')
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    product['title'] = title_link.get_text(strip=True)
                    product['url'] = 'https://amazon.com' + title_link.get('href', '')
            
            # Price information from search results
            pricing = self._extract_pricing_from_search(container)
            product['pricing'] = pricing
            
            # More buying choices
            buying_choices = self._extract_buying_choices(container)
            if buying_choices:
                product['buying_choices'] = buying_choices
            
            # Prime info
            prime_element = container.find('i', class_='a-icon-prime')
            product['prime'] = bool(prime_element)
            
            # Delivery info
            delivery_info = self._extract_delivery_info(container)
            if delivery_info:
                product['delivery'] = delivery_info
            
            # Ratings
            rating_info = self._extract_rating_info(container)
            if rating_info:
                product['rating'] = rating_info
            
            return product if product.get('asin') else None
            
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None
    
    def _extract_pricing_from_search(self, container) -> Dict:
        """Extract all pricing information from search results"""
        pricing = {
            'current_price': None,
            'list_price': None,
            'discount_percentage': None,
            'coupon': None,
            'raw_price_text': None
        }
        
        try:
            # Get the main price container
            price_container = container.find('span', class_='a-price')
            if price_container:
                # Current price
                current_price_element = price_container.find('span', class_='a-offscreen')
                if current_price_element:
                    pricing['current_price'] = current_price_element.get_text(strip=True)
            
            # List price (strikethrough)
            list_price_elements = container.find_all('span', {'data-a-strike': 'true'})
            for element in list_price_elements:
                price_text = element.get_text(strip=True)
                if 'List:' in price_text or '$' in price_text:
                    pricing['list_price'] = price_text
                    break
            
            # Look for discount percentage
            discount_element = container.find('span', class_='a-color-price')
            if discount_element:
                discount_text = discount_element.get_text(strip=True)
                if '%' in discount_text:
                    pricing['discount_percentage'] = discount_text
            
            # Look for coupon
            coupon_element = container.find('span', text=lambda x: x and 'coupon' in x.lower())
            if coupon_element:
                pricing['coupon'] = coupon_element.get_text(strip=True)
            
            # Capture raw price area text for debugging
            price_area = container.find('span', class_='a-price-range')
            if price_area:
                pricing['raw_price_text'] = price_area.get_text(strip=True)
            
        except Exception as e:
            print(f"Error extracting pricing: {e}")
        
        return pricing
    
    def _extract_buying_choices(self, container) -> Optional[Dict]:
        """Extract 'More Buying Choices' information"""
        try:
            # Look for "More Buying Choices" text and associated price
            buying_choices_text = container.find('span', text=lambda x: x and 'buying choices' in x.lower())
            if buying_choices_text:
                # Get the parent container and look for price info
                parent = buying_choices_text.parent
                if parent:
                    price_info = parent.get_text(strip=True)
                    return {
                        'available': True,
                        'text': price_info
                    }
            
            # Alternative: Look for additional offer information
            offer_element = container.find('span', text=lambda x: x and ('new' in x.lower() or 'used' in x.lower()) and 'offer' in x.lower())
            if offer_element:
                return {
                    'available': True,
                    'text': offer_element.get_text(strip=True)
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting buying choices: {e}")
            return None
    
    def _extract_delivery_info(self, container) -> Optional[Dict]:
        """Extract delivery information"""
        try:
            delivery_info = {}
            
            # Look for delivery text
            delivery_elements = container.find_all('span', text=lambda x: x and any(
                word in x.lower() for word in ['delivery', 'arrives', 'get it by', 'free']
            ))
            
            for element in delivery_elements:
                delivery_text = element.get_text(strip=True)
                if 'FREE' in delivery_text.upper():
                    delivery_info['free_delivery'] = delivery_text
                elif any(word in delivery_text.lower() for word in ['arrives', 'get it by']):
                    delivery_info['arrival_date'] = delivery_text
            
            return delivery_info if delivery_info else None
            
        except Exception as e:
            print(f"Error extracting delivery info: {e}")
            return None
    
    def _extract_rating_info(self, container) -> Optional[Dict]:
        """Extract rating information"""
        try:
            rating_info = {}
            
            # Star rating
            rating_element = container.find('span', class_='a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                if 'out of' in rating_text:
                    rating_info['rating_text'] = rating_text
            
            # Number of reviews
            review_element = container.find('a', class_='a-link-normal')
            if review_element:
                review_text = review_element.get_text(strip=True)
                if review_text.replace(',', '').isdigit():
                    rating_info['review_count'] = review_text
            
            return rating_info if rating_info else None
            
        except Exception as e:
            print(f"Error extracting rating info: {e}")
            return None
    
    def save_results(self, results: Dict, filename: Optional[str] = None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            search_term = results.get('search_term', 'unknown').replace(' ', '_')
            filename = f"amazon_search_prices_{search_term}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return None


def main():
    """Main function for testing"""
    extractor = AmazonSearchPriceExtractor()
    
    # Test with gaming chair
    search_term = "gaming chair"
    results = extractor.search_and_extract_prices(search_term, max_results=5)
    
    # Print results
    print("\n" + "="*60)
    print("🎯 PRICE EXTRACTION RESULTS")
    print("="*60)
    
    for i, product in enumerate(results.get('products', []), 1):
        print(f"\n📦 Product {i}:")
        print(f"   ASIN: {product.get('asin', 'N/A')}")
        print(f"   Title: {product.get('title', 'N/A')[:60]}...")
        
        pricing = product.get('pricing', {})
        print(f"   Current Price: {pricing.get('current_price', 'N/A')}")
        print(f"   List Price: {pricing.get('list_price', 'N/A')}")
        print(f"   Discount: {pricing.get('discount_percentage', 'N/A')}")
        print(f"   Coupon: {pricing.get('coupon', 'N/A')}")
        
        if product.get('buying_choices'):
            print(f"   More Buying Choices: {product['buying_choices']['text']}")
        
        if product.get('prime'):
            print(f"   Prime: ✅")
        
        delivery = product.get('delivery', {})
        if delivery:
            print(f"   Delivery: {delivery}")
    
    # Save results
    extractor.save_results(results)
    
    print(f"\n🎉 Extraction complete! Found {len(results.get('products', []))} products")


if __name__ == "__main__":
    main()
