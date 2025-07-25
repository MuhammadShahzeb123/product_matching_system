#!/usr/bin/env python3
"""
Enhanced Amazon Search-Based Price and Seller Extractor

This module extracts price information directly from Amazon search results,
which is more reliable than product detail pages for pricing and seller info.
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus

# Import scraping dependencies
try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

from bs4 import BeautifulSoup


class AmazonSearchBasedExtractor:
    """
    Enhanced Amazon extractor that gets price and seller info from search results
    instead of individual product pages for better reliability.
    """
    
    def __init__(self, use_proxy: bool = True):
        self.use_proxy = use_proxy
        self.setup_config()
    
    def setup_config(self):
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
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache'
        }
        
        if self.use_proxy:
            self.proxies = {
                "http": "http://250621Ev04e-resi_region-US_California:5PjDM1IoS0JSr2c@ca.proxy-jet.io:1010",
                "https": "http://250621Ev04e-resi_region-US_California:5PjDM1IoS0JSr2c@ca.proxy-jet.io:1010"
            }
        else:
            self.proxies = None
        
        self.timeout = 30
    
    def extract_products_from_search(self, search_term: str, max_results: int = 10) -> List[Dict]:
        """
        Extract product information from Amazon search results.
        
        This method gets price and seller info directly from search pages,
        which is more reliable than individual product pages.
        """
        print(f"🔍 Extracting products from search: '{search_term}'")
        print(f"📊 Target: {max_results} products")
        
        # Get search results HTML
        html_content = self._fetch_search_results(search_term)
        if not html_content:
            print("❌ Failed to fetch search results")
            return []
        
        # Parse search results
        products = self._parse_search_page(html_content, max_results)
        
        print(f"✅ Extracted {len(products)} products from search results")
        return products
    
    def get_product_from_asin(self, asin: str) -> Optional[Dict]:
        """
        Get product info by searching for specific ASIN.
        This still uses search results instead of detail page.
        """
        print(f"🔍 Searching for ASIN: {asin}")
        
        # Search for the specific ASIN
        search_term = asin
        html_content = self._fetch_search_results(search_term)
        if not html_content:
            print("❌ Failed to fetch search results for ASIN")
            return None
        
        # Parse and find the exact ASIN
        products = self._parse_search_page(html_content, max_results=20)
        
        # Find the matching ASIN
        for product in products:
            if product.get('asin') == asin:
                print(f"✅ Found product for ASIN: {asin}")
                return product
        
        print(f"⚠️ Product with ASIN {asin} not found in search results")
        return None
    
    def _fetch_search_results(self, search_term: str) -> Optional[str]:
        """Fetch Amazon search results HTML"""
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
                print(f"✅ Fetched search results ({len(response.text):,} chars)")
                return response.text
            else:
                print(f"❌ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching search results: {e}")
            return None
    
    def _parse_search_page(self, html_content: str, max_results: int) -> List[Dict]:
        """Parse search results page and extract product data"""
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
                    product_data = self._extract_search_product_data(container)
                    if product_data and product_data.get('asin'):
                        products.append(product_data)
                        title = product_data.get('basic_info', {}).get('name', 'N/A')
                        print(f"  ✓ Product {i+1}: {title[:50]}...")
                    else:
                        print(f"  ⚠ Product {i+1}: No valid data extracted")
                        
                except Exception as e:
                    print(f"  ❌ Product {i+1}: Error - {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"❌ Error parsing search results: {e}")
            return []
    
    def _extract_search_product_data(self, container) -> Optional[Dict]:
        """Extract comprehensive product data from search result container"""
        try:
            product = {
                'extraction_source': 'amazon_search_results',
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # Basic identifiers
            product['asin'] = container.get('data-asin', '')
            if not product['asin']:
                return None
            
            # Basic info
            basic_info = self._extract_basic_info(container)
            if basic_info:
                product['basic_info'] = basic_info
            
            # Pricing from search results
            pricing = self._extract_search_pricing(container)
            if pricing:
                product['pricing'] = pricing
            
            # Seller and fulfillment info
            seller_info = self._extract_seller_info_from_search(container)
            if seller_info:
                product['seller_info'] = seller_info
            
            # Reviews and ratings
            reviews = self._extract_review_info(container)
            if reviews:
                product['reviews'] = reviews
            
            # Prime and delivery
            shipping = self._extract_shipping_info(container)
            if shipping:
                product['shipping'] = shipping
            
            # Additional features
            features = self._extract_search_features(container)
            if features:
                product['features'] = features
            
            return product
            
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None
    
    def _extract_basic_info(self, container) -> Dict:
        """Extract basic product information"""
        basic_info = {}
        
        try:
            # Product title - try multiple selectors
            title_selectors = [
                'h2 a span',
                'h2 span',
                '[data-cy="title-recipe-label"]',
                '.a-size-medium.a-color-base',
                '.a-size-base-plus'
            ]
            
            for selector in title_selectors:
                title_element = container.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    if title and len(title) > 10:  # Valid title should be reasonably long
                        basic_info['name'] = title
                        break
            
            # If still no title, try a broader approach
            if not basic_info.get('name'):
                h2_element = container.find('h2')
                if h2_element:
                    # Get all text from h2, clean it up
                    title_text = h2_element.get_text(strip=True)
                    if title_text and len(title_text) > 10:
                        basic_info['name'] = title_text
            
            # Product URL
            link_element = container.find('h2')
            if link_element:
                link = link_element.find('a')
                if link and link.get('href'):
                    basic_info['url'] = 'https://amazon.com' + link.get('href')
            
            # Image
            img_element = container.find('img', class_='s-image')
            if img_element:
                basic_info['image_url'] = img_element.get('src', '')
                basic_info['image_alt'] = img_element.get('alt', '')
            
        except Exception as e:
            print(f"Error extracting basic info: {e}")
        
        return basic_info
    
    def _extract_search_pricing(self, container) -> Dict:
        """Extract comprehensive pricing information from search results"""
        pricing = {
            'currency': 'USD',
            'price_source': 'search_results'
        }
        
        try:
            # Current/Main price
            price_element = container.find('span', class_='a-price')
            if price_element:
                current_price = price_element.find('span', class_='a-offscreen')
                if current_price:
                    price_text = current_price.get_text(strip=True)
                    pricing['current_price'] = price_text
                    pricing['formatted_current_price'] = price_text
                    
                    # Extract numeric value
                    price_value = self._extract_price_value(price_text)
                    if price_value:
                        pricing['price'] = price_value
            
            # List price (was/original price)
            list_price_element = container.find('span', {'data-a-strike': 'true'})
            if list_price_element:
                list_price_text = list_price_element.get_text(strip=True)
                if list_price_text:
                    # Clean up the list price text (remove "List:" prefix and duplicates)
                    cleaned_list_price = re.sub(r'^List:\s*', '', list_price_text)
                    # Remove duplicate price (e.g., "$179.99$179.99" -> "$179.99")
                    price_pattern = r'(\$[\d,]+\.?\d*)'
                    matches = re.findall(price_pattern, cleaned_list_price)
                    if matches:
                        cleaned_list_price = matches[0]  # Take the first match
                    
                    pricing['list_price'] = cleaned_list_price
                    pricing['was_price'] = cleaned_list_price
            
            # Discount percentage
            discount_element = container.find('span', class_=re.compile(r'.*percent.*'))
            if not discount_element:
                # Look for percentage in any text
                percent_elements = container.find_all(string=re.compile(r'\d+%'))
                if percent_elements:
                    pricing['discount_percentage'] = percent_elements[0].strip()
            else:
                pricing['discount_percentage'] = discount_element.get_text(strip=True)
            
            # Coupon information
            coupon_elements = container.find_all(string=re.compile(r'coupon', re.IGNORECASE))
            for coupon_text in coupon_elements:
                coupon_str = coupon_text.strip()
                if coupon_str and ('off' in coupon_str.lower() or 'save' in coupon_str.lower()):
                    pricing['coupon'] = coupon_str
                    break
            
            # More buying choices
            buying_choices = self._extract_buying_choices_from_search(container)
            if buying_choices:
                pricing['more_buying_choices'] = buying_choices
            
        except Exception as e:
            print(f"Error extracting pricing: {e}")
        
        return pricing
    
    def _extract_buying_choices_from_search(self, container) -> Optional[Dict]:
        """Extract 'More Buying Choices' from search results"""
        try:
            # Look for buying choices text patterns
            buying_choice_patterns = [
                r'\$[\d,]+\.?\d*\s*\(\d+\+?\s*(?:used|new)\s*&?\s*(?:new|used)?\s*offers?\)',
                r'\(\d+\+?\s*(?:used|new)\s*&?\s*(?:new|used)?\s*offers?\)'
            ]
            
            all_text = container.get_text()
            for pattern in buying_choice_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    return {
                        'available': True,
                        'text': match.group().strip()
                    }
            
            return None
            
        except Exception as e:
            print(f"Error extracting buying choices: {e}")
            return None
    
    def _extract_seller_info_from_search(self, container) -> Dict:
        """Extract seller and fulfillment information from search results"""
        seller_info = {}
        
        try:
            # Prime eligibility
            prime_element = container.find('i', class_='a-icon-prime')
            seller_info['prime_eligible'] = bool(prime_element)
            
            # Try to determine fulfillment type from search results
            if seller_info['prime_eligible']:
                seller_info['fulfillment_type'] = 'FBA'  # Prime usually means FBA
            
            # Look for seller information in search results
            # This is limited in search results, but we can try
            seller_text_elements = container.find_all(string=re.compile(r'by\s+\w+', re.IGNORECASE))
            for text in seller_text_elements:
                if 'by ' in text.lower():
                    potential_seller = text.strip()
                    if len(potential_seller) < 100:  # Reasonable seller name length
                        seller_info['seller_name'] = potential_seller
                        break
            
        except Exception as e:
            print(f"Error extracting seller info: {e}")
        
        return seller_info
    
    def _extract_review_info(self, container) -> Dict:
        """Extract review and rating information"""
        reviews = {}
        
        try:
            # Star rating
            rating_element = container.find('span', class_='a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                if 'out of' in rating_text:
                    reviews['rating_text'] = rating_text
                    # Extract numeric rating
                    rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
                    if rating_match:
                        reviews['rating'] = float(rating_match.group(1))
            
            # Number of reviews
            review_count_elements = container.find_all(string=re.compile(r'\d{1,3}(?:,\d{3})*'))
            for text in review_count_elements:
                # Check if it looks like a review count (number in parentheses or after rating)
                if text.replace(',', '').isdigit():
                    count = int(text.replace(',', ''))
                    if count > 0 and count < 1000000:  # Reasonable review count range
                        reviews['review_count'] = count
                        reviews['formatted_review_count'] = text
                        break
            
        except Exception as e:
            print(f"Error extracting review info: {e}")
        
        return reviews
    
    def _extract_shipping_info(self, container) -> Dict:
        """Extract shipping and delivery information"""
        shipping = {}
        
        try:
            # Free delivery
            free_delivery_elements = container.find_all(string=re.compile(r'FREE', re.IGNORECASE))
            for text in free_delivery_elements:
                if 'delivery' in text.lower() or 'shipping' in text.lower():
                    shipping['free_delivery'] = text.strip()
                    break
            
            # Delivery date
            delivery_patterns = [
                r'Get it by \w+, \w+ \d+',
                r'Arrives \w+, \w+ \d+',
                r'Delivery \w+, \w+ \d+'
            ]
            
            all_text = container.get_text()
            for pattern in delivery_patterns:
                match = re.search(pattern, all_text)
                if match:
                    shipping['delivery_estimate'] = match.group().strip()
                    break
            
        except Exception as e:
            print(f"Error extracting shipping info: {e}")
        
        return shipping
    
    def _extract_search_features(self, container) -> Dict:
        """Extract additional features from search results"""
        features = {}
        
        try:
            # Sustainability features
            sustainability_elements = container.find_all(string=re.compile(r'sustainability', re.IGNORECASE))
            if sustainability_elements:
                features['sustainability'] = sustainability_elements[0].strip()
            
            # Climate pledge friendly
            climate_elements = container.find_all(string=re.compile(r'climate pledge', re.IGNORECASE))
            if climate_elements:
                features['climate_pledge_friendly'] = True
            
            # Amazon's Choice
            choice_elements = container.find_all(string=re.compile(r"amazon's choice", re.IGNORECASE))
            if choice_elements:
                features['amazons_choice'] = True
            
        except Exception as e:
            print(f"Error extracting features: {e}")
        
        return features
    
    def _extract_price_value(self, price_text: str) -> Optional[float]:
        """Extract numeric value from price text"""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.]', '', price_text)
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None
    
    def save_search_results(self, products: List[Dict], search_term: str) -> str:
        """Save search results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_search_results_{search_term.replace(' ', '_')}_{timestamp}.json"
        
        result_data = {
            'search_term': search_term,
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_source': 'amazon_search_results',
            'products_found': len(products),
            'products': products
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Search results saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return ""


def test_search_extractor():
    """Test the search-based extractor"""
    extractor = AmazonSearchBasedExtractor(use_proxy=True)
    
    print("🚀 Testing Amazon Search-Based Price Extractor")
    print("="*60)
    
    # Test search extraction
    products = extractor.extract_products_from_search("gaming chair", max_results=3)
    
    if products:
        print("\n📊 EXTRACTED PRODUCTS:")
        print("="*60)
        
        for i, product in enumerate(products, 1):
            print(f"\n🛍️ Product {i}:")
            print(f"   ASIN: {product.get('asin', 'N/A')}")
            
            basic_info = product.get('basic_info', {})
            print(f"   Title: {basic_info.get('name', 'N/A')[:60]}...")
            
            pricing = product.get('pricing', {})
            print(f"   Current Price: {pricing.get('current_price', 'N/A')}")
            print(f"   List Price: {pricing.get('list_price', 'N/A')}")
            
            if pricing.get('coupon'):
                print(f"   Coupon: {pricing['coupon']}")
            
            if pricing.get('more_buying_choices'):
                print(f"   More Buying Choices: {pricing['more_buying_choices']['text']}")
            
            seller_info = product.get('seller_info', {})
            if seller_info.get('prime_eligible'):
                print(f"   Prime: ✅")
            
            reviews = product.get('reviews', {})
            if reviews.get('rating'):
                print(f"   Rating: {reviews['rating']}/5 ({reviews.get('formatted_review_count', 'N/A')} reviews)")
        
        # Save results
        extractor.save_search_results(products, "gaming_chair")
        
    else:
        print("❌ No products extracted")


if __name__ == "__main__":
    test_search_extractor()
