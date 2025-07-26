# Target Search Scraper Module

## Overview

This module provides a complete Target.com search and scraping solution that has been extracted from the main product matching system. It offers both search functionality and direct URL scraping capabilities with intelligent search strategies.

## Features

### 🎯 **Search Functionality**
- Search Target.com products by query terms
- Intelligent search strategies (UPC → Title+Brand → Brand → Fallback)
- UPC/barcode search support for exact product matches
- Automatic result validation and filtering

### 🔗 **URL Scraping**
- Scrape detailed product information from Target product URLs
- Support for any Target product page
- Comprehensive product data extraction

### 🧠 **Intelligent Search**
- Amazon product-based intelligent Target search
- Multiple search strategies with automatic fallback
- UPC extraction and cleaning
- Brand and title optimization for Target search

### 💾 **Data Management**
- Automatic JSON file saving for all results
- Timestamped result files
- Organized directory structure
- Optional save/no-save modes

## Installation & Setup

1. **Place the module** in your project directory:
   ```
   target_search_scraper.py
   ```

2. **Dependencies** (already present in your project):
   ```python
   # Required modules (should already exist)
   from target_complete_fetcher_parser import TargetProductExtractor
   from unneeded.dynamic_target_scraper import TargetScraper  # Optional
   ```

3. **Directory structure** (auto-created):
   ```
   target_search_results/  # Auto-created for saving results
   ```

## Usage Examples

### 🔍 **Basic Search**
```python
from target_search_scraper import TargetSearchScraper

# Initialize scraper
scraper = TargetSearchScraper()

# Search for products
products = scraper.search_products("gaming chair", max_results=5)

# Results automatically saved to JSON file
print(f"Found {len(products)} products")
```

### 🎯 **URL Scraping**
```python
# Scrape specific product URL
url = "https://www.target.com/p/apple-airpods-3rd-generation/-/A-84529355"
product_data = scraper.scrape_product_url(url)

if product_data:
    basic_info = product_data.get('basic_info', {})
    print(f"Product: {basic_info.get('name')}")
    print(f"Price: {basic_info.get('price')}")
```

### 🧠 **Intelligent Search (Amazon-based)**
```python
# Use Amazon product data to intelligently search Target
amazon_product = {
    'title': 'Logitech G Pro Wireless Gaming Mouse',
    'brand': 'Logitech',
    'specifications': {'UPC': '097855142146'}
}

# This will try UPC first, then title+brand, then brand, then fallback
target_products = scraper.intelligent_search(
    amazon_product, 
    fallback_term="gaming mouse",
    max_results=5
)
```

### 📦 **Batch Processing**
```python
# Get detailed info for multiple products
search_results = scraper.search_products("bluetooth speaker", max_results=3)
detailed_products = scraper.get_detailed_products(search_results)

print(f"Got detailed info for {len(detailed_products)} products")
```

### 🎈 **Convenience Functions**
```python
# Quick one-line functions
from target_search_scraper import search_target_products, scrape_target_url

# Quick search
products = search_target_products("office chair", max_results=3)

# Quick URL scrape
product = scrape_target_url("https://www.target.com/p/...")
```

## Integration with Main System

The main `product_matching_system.py` has been updated to use this module:

```python
# The main system now uses the new Target scraper
from target_search_scraper import TargetSearchScraper

class ProductMatchingSystem:
    def __init__(self):
        # Old: self.target_searcher = TargetScraper(...)
        # New: self.target_scraper = TargetSearchScraper(...)
        self.target_scraper = TargetSearchScraper(proxy_config=self.proxy_config)
    
    def _search_target_products(self, search_term, max_results=5):
        # Now uses the new module
        return self.target_scraper.search_products(search_term, max_results, save_results=False)
```

## Search Strategies

### 🎯 **Intelligent Search Priority**
1. **UPC/Barcode Search** (Highest precision)
   - Extracts UPC/GTIN/EAN from Amazon product
   - Cleans and validates barcode format
   - Direct product match

2. **Title + Brand Search** (High precision)
   - Combines Amazon title with brand name
   - Removes noise words, keeps important descriptors
   - Good for finding same products

3. **Brand Only Search** (Medium precision)
   - Searches just the brand name
   - Useful when title is too specific

4. **Fallback Search** (Base precision)
   - Uses provided fallback term
   - Last resort option

### 🔍 **Search Validation**
- UPC results are validated for relevance
- Keyword overlap analysis
- Brand matching verification
- Product type similarity checks

## File Output Structure

### 📁 **Search Results**
```json
{
  "search_type": "basic_search",
  "search_term": "gaming chair",
  "timestamp": "20250726_143052",
  "total_products": 5,
  "products": [...]
}
```

### 📁 **Product Details**
```json
{
  "basic_info": {
    "name": "Product Name",
    "tcin": "84529355",
    "brand": "Apple",
    "price": "$179.99"
  },
  "technical_specs": {...},
  "scrape_timestamp": "2025-07-26T14:30:52",
  "source_url": "https://www.target.com/p/..."
}
```

### 📁 **Intelligent Search Results**
```json
{
  "search_type": "intelligent_search",
  "amazon_product_reference": {
    "title": "Logitech G Pro Wireless Gaming Mouse",
    "brand": "Logitech",
    "asin": "B07GBZ4Q68"
  },
  "successful_strategy": "UPC/Barcode search",
  "products": [...]
}
```

## Command Line Interface

```bash
# Search mode
python target_search_scraper.py --search "gaming chair" --max-results 5

# URL scraping mode  
python target_search_scraper.py --url "https://www.target.com/p/..."

# Interactive mode
python target_search_scraper.py
```

## Testing

Run the test suite to verify functionality:

```bash
python test_target_scraper.py
```

The test will check:
- ✅ Module import and initialization
- ✅ Search functionality (if available)
- ✅ URL scraping capability
- ✅ Integration with main system
- ✅ Convenience functions

## Configuration

### 🔧 **Proxy Configuration**
```python
proxy_config = {
    "url": "http://user:pass@proxy:port",
    "http": "http://user:pass@proxy:port",
    "https": "https://user:pass@proxy:port"
}

scraper = TargetSearchScraper(proxy_config=proxy_config, use_proxy=True)
```

### 🔧 **No Proxy Mode**
```python
scraper = TargetSearchScraper(use_proxy=False)
```

## Error Handling

The module handles various error conditions:
- ❌ Target search module not available → URL scraping only
- ❌ Network/proxy errors → Graceful fallback
- ❌ Invalid URLs → Clear error messages
- ❌ Search failures → Empty result with logs

## Migration from Old System

### 🔄 **What Changed**
- **Removed** from `product_matching_system.py`:
  - `_create_intelligent_target_search_query()`
  - `_validate_upc_search_results()`
  - Target search initialization code
  - Target search-specific imports

- **Added** new module:
  - `target_search_scraper.py` - Complete Target functionality
  - Improved error handling and logging
  - JSON result saving
  - Command line interface

### 🔄 **Compatibility**
- Main system API remains the same
- All existing functionality preserved
- Enhanced with better error handling
- Results now automatically saved

## Benefits of Separation

1. **🧩 Modularity**: Target functionality is now self-contained
2. **🔧 Maintainability**: Easier to update Target-specific code
3. **🧪 Testability**: Can test Target functionality independently
4. **♻️ Reusability**: Module can be used in other projects
5. **📊 Better Logging**: Detailed operation logging and result saving
6. **🎯 Focus**: Main system focuses on matching, Target module focuses on scraping

## Troubleshooting

### ⚠️ **"Target search module not available"**
- The `unneeded.dynamic_target_scraper` module is missing
- URL scraping will still work
- Search functionality will be disabled

### ⚠️ **Network/Proxy Errors**
- Check proxy configuration
- Try `use_proxy=False` mode
- Verify Target.com accessibility

### ⚠️ **No Search Results**
- Target might be blocking requests
- Try different search terms
- Check if Target search module is properly installed

### ⚠️ **Import Errors**
- Ensure `target_complete_fetcher_parser.py` exists
- Check Python path configuration
- Verify all dependencies are available
