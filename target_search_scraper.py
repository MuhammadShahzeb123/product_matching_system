#!/usr/bin/env python3
"""
Complete Target.com Search & Scraper Module

This module provides comprehensive Target.com functionality:
1. Search Target.com products by query terms
2. Scrape individual Target product URLs
3. Extract detailed product information
4. Save results to JSON files

Features:
- Intelligent search with UPC/barcode support
- Multiple search strategies (UPC -> Title+Brand -> Brand -> Fallback)
- Direct URL scraping for specific products
- Comprehensive error handling and rate limiting
- Automatic result saving to JSON files

Usage:
    from target_search_scraper import TargetSearchScraper
    
    # Initialize
    scraper = TargetSearchScraper()
    
    # Search for products
    products = scraper.search_products("gaming chair", max_results=5)
    
    # Scrape specific URL
    product_data = scraper.scrape_product_url("https://www.target.com/p/...")
    
    # Intelligent search based on Amazon product data
    products = scraper.intelligent_search(amazon_product_data, "fallback search term")
"""

import json
import os
import sys
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing Target modules
from target_complete_fetcher_parser import TargetProductExtractor

# Try to import Target search capabilities
try:
    from unneeded.dynamic_target_scraper import TargetScraper
    TARGET_SEARCH_AVAILABLE = True
    print("✅ Target search functionality available")
except ImportError:
    TargetScraper = None
    TARGET_SEARCH_AVAILABLE = False
    print("⚠️  Target search module not available. URL scraping only.")


class TargetSearchScraper:
    """
    Complete Target.com search and scraping functionality.
    
    Provides both search capabilities and direct URL scraping with
    intelligent search strategies based on Amazon product data.
    """
    
    def __init__(self, proxy_config: Optional[Dict] = None, use_proxy: bool = True):
        """
        Initialize the Target Search Scraper.
        
        Args:
            proxy_config: Optional proxy configuration
            use_proxy: Whether to use proxy for requests
        """
        self.proxy_config = proxy_config
        self.use_proxy = use_proxy
        
        # Initialize Target product extractor (for URL scraping)
        self.target_extractor = TargetProductExtractor()
        
        # Initialize Target searcher (for search functionality)
        self.target_searcher = None
        if TARGET_SEARCH_AVAILABLE and TargetScraper is not None:
            try:
                self.target_searcher = self._initialize_target_searcher()
                print("✅ Target search functionality initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize Target searcher: {str(e)}")
        
        # Create results directory
        self.results_dir = Path("target_search_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _initialize_target_searcher(self) -> Optional[Any]:
        """Initialize Target scraper with fallback options"""
        if not TARGET_SEARCH_AVAILABLE or TargetScraper is None:
            return None
            
        try:
            # Try different initialization options
            if self.proxy_config:
                proxy_url = self.proxy_config.get("url", self.proxy_config.get("http"))
                return TargetScraper(proxy=proxy_url, use_proxy=self.use_proxy)
            else:
                return TargetScraper(use_proxy=self.use_proxy)
        except Exception as e:
            print(f"Failed to initialize Target searcher: {str(e)}")
            # Try without proxy as fallback
            try:
                return TargetScraper(use_proxy=False)
            except Exception as e2:
                print(f"Failed to initialize Target searcher without proxy: {str(e2)}")
                return None
    
    def search_products(self, search_term: str, max_results: int = 5, save_results: bool = True) -> List[Dict]:
        """
        Search Target for products using a search term.
        
        Args:
            search_term: Search query (e.g., "gaming chair", "bluetooth speaker")
            max_results: Maximum number of products to return
            save_results: Whether to save results to JSON file
            
        Returns:
            List of product dictionaries with basic search result info
        """
        print(f"🔍 Searching Target.com for: '{search_term}'")
        
        if not TARGET_SEARCH_AVAILABLE or TargetScraper is None or not self.target_searcher:
            print("❌ Target search functionality not available")
            return []
        
        try:
            # Perform search
            products = self.target_searcher.search_and_extract(search_term, max_results)
            
            if not products:
                print("❌ No products found in Target search")
                return []
            
            print(f"✅ Found {len(products)} Target products")
            
            # Convert to standardized dict format
            product_dicts = []
            for product in products:
                product_dict = {
                    'tcin': getattr(product, 'tcin', ''),
                    'title': getattr(product, 'title', ''),
                    'price': getattr(product, 'price', ''),
                    'original_price': getattr(product, 'original_price', ''),
                    'brand': getattr(product, 'brand', ''),
                    'product_url': getattr(product, 'product_url', ''),
                    'availability': getattr(product, 'availability', ''),
                    'image_url': getattr(product, 'image_url', ''),
                    'rating': getattr(product, 'rating', ''),
                    'review_count': getattr(product, 'review_count', ''),
                    'search_term': search_term,
                    'search_timestamp': datetime.now().isoformat()
                }
                product_dicts.append(product_dict)
            
            # Save results if requested
            if save_results:
                self._save_search_results(search_term, product_dicts)
            
            return product_dicts
            
        except Exception as e:
            print(f"❌ Target search error: {str(e)}")
            return []
    
    def scrape_product_url(self, product_url: str, save_results: bool = True) -> Optional[Dict]:
        """
        Scrape detailed product information from a Target product URL.
        
        Args:
            product_url: Full Target product URL
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary with detailed product information or None if failed
        """
        print(f"🎯 Scraping Target product: {product_url}")
        
        try:
            # Extract product data using existing Target extractor
            detailed_product = self.target_extractor.extract_product(product_url)
            
            if not detailed_product or 'error' in detailed_product:
                error_msg = detailed_product.get('error', 'Unknown error') if detailed_product else 'Failed to extract product'
                print(f"❌ Error scraping Target product: {error_msg}")
                return None
            
            # Add metadata
            detailed_product['scrape_timestamp'] = datetime.now().isoformat()
            detailed_product['source_url'] = product_url
            detailed_product['scrape_method'] = 'direct_url'
            
            print(f"✅ Successfully scraped Target product: {detailed_product.get('basic_info', {}).get('name', 'Unknown')[:60]}...")
            
            # Save results if requested
            if save_results:
                self._save_product_details(detailed_product)
            
            return detailed_product
            
        except Exception as e:
            print(f"❌ Error scraping Target URL: {str(e)}")
            return None
    
    def intelligent_search(self, amazon_product: Dict, base_search_term: str = "", max_results: int = 5, save_results: bool = True) -> List[Dict]:
        """
        Perform intelligent Target search based on Amazon product data.
        
        Uses multiple search strategies in order of precision:
        1. UPC/barcode search (most precise)
        2. Amazon title + brand search
        3. Brand only search  
        4. Base search term (fallback)
        
        Args:
            amazon_product: Amazon product data to use for creating search queries
            base_search_term: Fallback search term (e.g., "gaming chair")
            max_results: Maximum number of results to return
            save_results: Whether to save results to JSON file
            
        Returns:
            List of Target product dictionaries
        """
        print(f"🧠 Using intelligent Target search based on Amazon product data...")
        
        # Get prioritized search queries
        search_queries = self._create_intelligent_search_queries(amazon_product, base_search_term)
        
        if not search_queries:
            print("❌ No valid search queries generated")
            return []
        
        all_products = []
        successful_strategy = None
        
        # Try each search query in order of precision
        for i, query in enumerate(search_queries, 1):
            strategy_name = [
                "UPC/Barcode search",
                "Title + Brand search", 
                "Brand only search",
                "Base search term"
            ][min(i-1, 3)]
            
            print(f"\n📋 Strategy {i}/{len(search_queries)}: {strategy_name}")
            print(f"   Query: '{query[:80]}...' " if len(query) > 80 else f"   Query: '{query}'")
            
            try:
                # Search Target
                products = self.search_products(query, max_results, save_results=False)
                
                if products:
                    # For UPC search, validate that results are actually related
                    if i == 1 and len(query.strip()) >= 10 and query.strip().isdigit():
                        # Validate UPC search results
                        valid_products = self._validate_upc_search_results(products, query, amazon_product)
                        if valid_products:
                            print(f"   ✅ Found {len(valid_products)} valid UPC-matched products")
                            all_products.extend(valid_products)
                            successful_strategy = strategy_name
                            print("   🎯 UPC search successful - using these results as high-confidence matches")
                            break
                        else:
                            print(f"   🔍 UPC '{query}' returned unrelated products - trying next strategy...")
                            continue
                    else:
                        print(f"   ✅ Found {len(products)} products with {strategy_name}")
                        all_products.extend(products)
                        successful_strategy = strategy_name
                    
                    # If we have enough products, we can stop
                    if len(all_products) >= max_results:
                        break
                else:
                    print(f"   ❌ No products found with {strategy_name}")
                    
            except Exception as e:
                print(f"   ⚠️ Error with {strategy_name}: {str(e)}")
                continue
        
        # Remove duplicates while preserving order
        unique_products = []
        seen_tcins = set()
        
        for product in all_products:
            tcin = product.get('tcin', '')
            if tcin and tcin not in seen_tcins:
                seen_tcins.add(tcin)
                unique_products.append(product)
        
        # Limit to max_results
        final_products = unique_products[:max_results]
        
        # Add intelligent search metadata
        for product in final_products:
            product['intelligent_search'] = True
            product['successful_strategy'] = successful_strategy
            product['amazon_product_reference'] = {
                'title': amazon_product.get('title', '')[:100],
                'brand': amazon_product.get('brand', ''),
                'asin': amazon_product.get('asin', '')
            }
        
        print(f"\n📊 Intelligent search result: {len(final_products)} unique products found")
        if successful_strategy:
            print(f"🎯 Successful strategy: {successful_strategy}")
        
        # Save results if requested
        if save_results and final_products:
            self._save_intelligent_search_results(amazon_product, base_search_term, final_products)
        
        return final_products
    
    def _create_intelligent_search_queries(self, amazon_product: Dict, base_search_term: str = "") -> List[str]:
        """
        Create intelligent Target search queries based on Amazon product data.
        
        Strategy order (highest to lowest precision):
        1. UPC/barcode search (exact product match)
        2. Amazon title + brand search
        3. Brand only search
        4. Base search term (fallback)
        """
        search_queries = []
        
        # Strategy 1: UPC/Barcode search (highest precision)
        print("   🎯 Strategy 1: UPC/Barcode extraction...")
        upc_paths = [
            'specifications.UPC',
            'specifications.GTIN', 
            'specifications.EAN',
            'specifications.Global Trade Identification Number',
            'specifications.European Article Number',
            'matching_data.barcode',
            'barcode',
            'gtin',
            'upc'
        ]
        
        for path in upc_paths:
            upc = self._get_nested_value(amazon_product, path)
            if upc:
                # Clean UPC (remove special characters like ‎)
                cleaned_upc = re.sub(r'[^\d]', '', str(upc))
                if len(cleaned_upc) >= 10 and cleaned_upc.isdigit():
                    search_queries.append(cleaned_upc)
                    print(f"   ✅ Found UPC: {cleaned_upc}")
                    break
        
        # Strategy 2: Title + Brand search
        print("   🎯 Strategy 2: Title + Brand extraction...")
        amazon_title = amazon_product.get('title', '').strip()
        brand = (amazon_product.get('brand', '') or 
                amazon_product.get('specifications', {}).get('Brand Name', '')).strip()
        
        if amazon_title:
            # Create clean title query
            clean_title = self._clean_search_title(amazon_title)
            
            if brand and clean_title:
                title_brand_query = f"{clean_title} {brand}"
                search_queries.append(title_brand_query)
                print(f"   ✅ Created title+brand query: {title_brand_query[:60]}...")
            elif clean_title:
                search_queries.append(clean_title)
                print(f"   ✅ Created title query: {clean_title[:60]}...")
        
        # Strategy 3: Brand only search
        if brand and brand not in [q for q in search_queries]:
            search_queries.append(brand)
            print(f"   ✅ Added brand query: {brand}")
        
        # Strategy 4: Base search term (final fallback)
        if base_search_term and base_search_term not in search_queries:
            search_queries.append(base_search_term)
            print(f"   ✅ Added fallback query: {base_search_term}")
        
        print(f"   📊 Generated {len(search_queries)} search strategies")
        return search_queries
    
    def _clean_search_title(self, title: str) -> str:
        """
        Clean Amazon title for Target search.
        
        Removes common noise words and normalizes the title while preserving
        important product descriptors.
        """
        if not title:
            return ""
        
        # Convert to lowercase and remove special characters
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
        
        # Remove extra spaces
        clean_title = ' '.join(clean_title.split())
        
        # Remove common noise words but keep important descriptors
        noise_words = {
            'for', 'with', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 
            'of', 'to', 'from', 'that', 'this', 'will', 'can', 'is', 'are',
            'has', 'have', 'was', 'were', 'been', 'be', 'or', 'but', 'if'
        }
        
        # Keep words that are longer than 2 characters or are not noise words
        words = []
        for word in clean_title.split():
            if len(word) > 2 and word not in noise_words:
                words.append(word)
        
        # Limit to reasonable length for search
        return ' '.join(words[:8])  # Keep first 8 meaningful words
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except:
            return None
    
    def _validate_upc_search_results(self, products: List[Dict], upc_query: str, amazon_product: Dict) -> List[Dict]:
        """
        Validate that UPC search results are actually related to the Amazon product.
        
        This prevents matching completely unrelated products when Target's UPC search
        returns unrelated results.
        """
        if not products:
            return []
        
        # Extract key terms from Amazon product for validation
        amazon_title = amazon_product.get('title', '').lower()
        amazon_brand = (amazon_product.get('brand', '') or
                       amazon_product.get('specifications', {}).get('Brand Name', '')).lower()
        amazon_categories = amazon_product.get('categories', [])
        
        # Get key words from Amazon product
        amazon_keywords = set()
        if amazon_title:
            # Extract meaningful words (length > 3, not common words)
            words = amazon_title.replace('-', ' ').split()
            amazon_keywords.update([w for w in words if len(w) > 3 and 
                                  w not in ['with', 'that', 'this', 'will', 'have', 'from', 'they']])
        
        if amazon_brand:
            amazon_keywords.add(amazon_brand.strip())
        
        # Add category keywords
        for cat in amazon_categories:
            if isinstance(cat, str):
                amazon_keywords.add(cat.lower())
        
        valid_products = []
        
        for product in products:
            # Extract Target product info
            target_title = product.get('title', '').lower()
            target_brand = product.get('brand', '').lower()
            
            # Calculate keyword overlap
            target_keywords = set()
            if target_title:
                words = target_title.replace('-', ' ').split()
                target_keywords.update([w for w in words if len(w) > 3])
            
            if target_brand:
                target_keywords.add(target_brand.strip())
            
            # Check for meaningful overlap
            overlap = amazon_keywords.intersection(target_keywords)
            
            # Consider valid if:
            # 1. Brands match, OR
            # 2. At least 2 meaningful keywords overlap, OR  
            # 3. Product types seem related
            if (amazon_brand and target_brand and amazon_brand == target_brand) or \
               (len(overlap) >= 2) or \
               (self._check_product_type_similarity(amazon_title, target_title)):
                valid_products.append(product)
            else:
                print(f"      🚫 Filtered out unrelated product: {target_title[:50]}...")
        
        return valid_products
    
    def _check_product_type_similarity(self, amazon_title: str, target_title: str) -> bool:
        """Check if Amazon and Target products are of similar types"""
        # Extract potential product type keywords
        type_keywords = {
            'chair', 'table', 'desk', 'bed', 'sofa', 'couch', 'dresser',
            'phone', 'laptop', 'computer', 'tablet', 'headphone', 'speaker',
            'kitchen', 'appliance', 'dishwasher', 'microwave', 'refrigerator',
            'clothing', 'shirt', 'pants', 'shoes', 'boots', 'jacket',
            'book', 'game', 'toy', 'tool', 'camera', 'watch'
        }
        
        amazon_types = set()
        target_types = set()
        
        for keyword in type_keywords:
            if keyword in amazon_title.lower():
                amazon_types.add(keyword)
            if keyword in target_title.lower():
                target_types.add(keyword)
        
        # Check for overlap in product types
        return len(amazon_types.intersection(target_types)) > 0
    
    def get_detailed_products(self, product_list: List[Dict], save_results: bool = True) -> List[Dict]:
        """
        Fetch detailed information for a list of products.
        
        Args:
            product_list: List of basic product info dicts (with product_url)
            save_results: Whether to save detailed results
            
        Returns:
            List of detailed product dictionaries
        """
        print(f"📊 Fetching detailed information for {len(product_list)} products...")
        
        detailed_products = []
        
        for i, product in enumerate(product_list, 1):
            product_url = product.get('product_url')
            if not product_url:
                print(f"   ⚠️ Product {i}/{len(product_list)}: No URL available")
                continue
            
            print(f"   📋 Fetching details {i}/{len(product_list)}...")
            detailed_product = self.scrape_product_url(product_url, save_results=False)
            
            if detailed_product:
                # Add original search metadata if available
                if 'search_term' in product:
                    detailed_product['original_search_term'] = product['search_term']
                if 'intelligent_search' in product:
                    detailed_product['intelligent_search'] = product['intelligent_search']
                    detailed_product['successful_strategy'] = product.get('successful_strategy')
                
                detailed_products.append(detailed_product)
            
            # Rate limiting
            time.sleep(2)
        
        print(f"✅ Successfully fetched details for {len(detailed_products)} products")
        
        # Save batch results if requested
        if save_results and detailed_products:
            self._save_detailed_batch_results(detailed_products)
        
        return detailed_products
    
    def _save_search_results(self, search_term: str, products: List[Dict]) -> None:
        """Save search results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"target_search_{search_term.replace(' ', '_')}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        result_data = {
            'search_type': 'basic_search',
            'search_term': search_term,
            'timestamp': timestamp,
            'total_products': len(products),
            'products': products
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Search results saved: {filepath}")
    
    def _save_product_details(self, product_data: Dict) -> None:
        """Save individual product details to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tcin = product_data.get('basic_info', {}).get('tcin', 'unknown')
        product_name = product_data.get('basic_info', {}).get('name', 'unknown')[:30]
        clean_name = re.sub(r'[^\w\s]', '', product_name).replace(' ', '_')
        
        filename = f"target_product_{tcin}_{clean_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Product details saved: {filepath}")
    
    def _save_intelligent_search_results(self, amazon_product: Dict, base_search_term: str, products: List[Dict]) -> None:
        """Save intelligent search results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        amazon_title = amazon_product.get('title', 'unknown')[:30]
        clean_title = re.sub(r'[^\w\s]', '', amazon_title).replace(' ', '_')
        
        filename = f"target_intelligent_search_{clean_title}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        result_data = {
            'search_type': 'intelligent_search',
            'amazon_product_reference': {
                'title': amazon_product.get('title', ''),
                'brand': amazon_product.get('brand', ''),
                'asin': amazon_product.get('asin', '')
            },
            'base_search_term': base_search_term,
            'timestamp': timestamp,
            'total_products': len(products),
            'successful_strategy': products[0].get('successful_strategy') if products else None,
            'products': products
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Intelligent search results saved: {filepath}")
    
    def _save_detailed_batch_results(self, detailed_products: List[Dict]) -> None:
        """Save batch of detailed products to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"target_detailed_batch_{len(detailed_products)}_products_{timestamp}.json"
        filepath = self.results_dir / filename
        
        result_data = {
            'result_type': 'detailed_batch',
            'timestamp': timestamp,
            'total_products': len(detailed_products),
            'products': detailed_products
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed batch results saved: {filepath}")


# Convenience functions for easy usage
def search_target_products(search_term: str, max_results: int = 5, save_results: bool = True) -> List[Dict]:
    """
    Convenience function to search Target products.
    
    Args:
        search_term: Search query
        max_results: Maximum number of results
        save_results: Whether to save results to file
        
    Returns:
        List of product dictionaries
    """
    scraper = TargetSearchScraper()
    return scraper.search_products(search_term, max_results, save_results)


def scrape_target_url(product_url: str, save_results: bool = True) -> Optional[Dict]:
    """
    Convenience function to scrape a Target product URL.
    
    Args:
        product_url: Target product URL
        save_results: Whether to save results to file
        
    Returns:
        Product data dictionary or None if failed
    """
    scraper = TargetSearchScraper()
    return scraper.scrape_product_url(product_url, save_results)


def intelligent_target_search(amazon_product: Dict, fallback_term: str = "", max_results: int = 5) -> List[Dict]:
    """
    Convenience function for intelligent Target search based on Amazon product.
    
    Args:
        amazon_product: Amazon product data dictionary
        fallback_term: Fallback search term if Amazon-based search fails
        max_results: Maximum number of results
        
    Returns:
        List of Target product dictionaries
    """
    scraper = TargetSearchScraper()
    return scraper.intelligent_search(amazon_product, fallback_term, max_results)


if __name__ == "__main__":
    """Command line interface for Target Search Scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Target.com Search & Scraper")
    parser.add_argument("--search", help="Search term for Target products")
    parser.add_argument("--url", help="Target product URL to scrape")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum search results (default: 5)")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to files")
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = TargetSearchScraper()
    save_results = not args.no_save
    
    if args.search:
        # Search mode
        print(f"🔍 Target Search Mode: '{args.search}'")
        products = scraper.search_products(args.search, args.max_results, save_results)
        
        if products:
            print(f"\n✅ Found {len(products)} products:")
            for i, product in enumerate(products, 1):
                print(f"   {i}. {product.get('title', 'No title')[:60]}...")
                print(f"      Price: {product.get('price', 'N/A')} | TCIN: {product.get('tcin', 'N/A')}")
        else:
            print("❌ No products found")
    
    elif args.url:
        # URL scraping mode
        print(f"🎯 Target URL Scraping Mode")
        product_data = scraper.scrape_product_url(args.url, save_results)
        
        if product_data:
            basic_info = product_data.get('basic_info', {})
            print(f"\n✅ Successfully scraped product:")
            print(f"   Name: {basic_info.get('name', 'Unknown')}")
            print(f"   TCIN: {basic_info.get('tcin', 'Unknown')}")
            print(f"   Brand: {basic_info.get('brand', 'Unknown')}")
            print(f"   Price: {basic_info.get('price', 'Unknown')}")
        else:
            print("❌ Failed to scrape product")
    
    else:
        # Interactive mode
        print("🎯 Target Search & Scraper - Interactive Mode")
        print("=" * 50)
        print("Choose an option:")
        print("1. Search for products")
        print("2. Scrape specific product URL")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            search_term = input("Enter search term: ").strip()
            if search_term:
                max_results = input("Max results (default 5): ").strip()
                max_results = int(max_results) if max_results.isdigit() else 5
                
                products = scraper.search_products(search_term, max_results, save_results)
                
                if products:
                    print(f"\n✅ Found {len(products)} products!")
                else:
                    print("\n❌ No products found")
            else:
                print("❌ No search term provided")
        
        elif choice == "2":
            url = input("Enter Target product URL: ").strip()
            if url:
                product_data = scraper.scrape_product_url(url, save_results)
                
                if product_data:
                    print("\n✅ Successfully scraped product!")
                else:
                    print("\n❌ Failed to scrape product")
            else:
                print("❌ No URL provided")
        
        else:
            print("❌ Invalid choice")
