# Product Matching System Context

## Current State (July 26, 2025)

- ✅ **Removed all sample data fallback systems**
- ✅ **Enhanced seller and shipment information extraction**
- ✅ **Implemented regex-based seller/shipment detection**
- ✅ **Now only uses live Target.com search results**
- ✅ **UPC cleaning and search strategy maintained**
- ✅ **FIXED: AttributeError in seller/shipment extraction** (July 26, 2025)

## Recent Major Changes Implemented

### 1. ✅ **FIXED: AttributeError 'dict' object has no attribute 'strip'**
- **🐛 Issue**: `_extract_enhanced_seller_shipment_info()` was trying to call `.strip()` on dict objects
- **✅ Fix**: Completely rewrote text source handling with safe string conversion
- **✅ New**: Added `source_paths` list with proper (name, value) tuples
- **✅ New**: Safe conversion handling for dicts, lists, and other objects
- **✅ New**: Enhanced validation to skip empty/meaningless text
- **✅ Removed**: Redundant `import re` (already imported at top of file)
- **✅ Clean**: More robust error handling with try/catch blocks

### 2. ✅ **REMOVED Sample Data Fallback System**
- **❌ Removed**: `_get_sample_target_products()` method completely
- **❌ Removed**: `_load_sample_target_product_details()` method completely
- **❌ Removed**: All fallback logic to local JSON files
- **✅ Updated**: `_search_target_products()` now only does live search
- **✅ Updated**: Error handling now returns empty lists instead of sample data
- **✅ Clean**: System now ONLY searches Target.com live - no local file fallbacks

### 2. ✅ **ENHANCED Seller & Shipment Information Extraction**
- **✅ New**: `_extract_enhanced_seller_shipment_info()` method with regex patterns
- **✅ New**: `_clean_seller_name()` method for cleaning extracted names
- **✅ Regex Patterns**:
  - `"Sold by * and Shipped by *"` - Main pattern requested by user
  - `"Ships from and sold by *"` - Alternative pattern
  - `"Sold by *"` - Seller-only pattern
  - `"Shipped by *"` - Shipper-only pattern
  - `"Ships from *"` - Alternative shipper pattern

### 3. ✅ **Intelligent Shipment Type Detection**
- **✅ Logic**: If `shipped by` contains "amazon" → "Shipped by Amazon"
- **✅ Logic**: If `shipped by` is NOT amazon → "Shipped by Seller"
- **✅ Clean**: Removes HTML tags, extra spaces, trailing punctuation from names

### 4. ✅ **Enhanced Reporting with Seller/Shipment Info**
- **✅ Updated**: `_generate_url_matching_report()` shows seller & shipment details
- **✅ Updated**: `_generate_matching_report()` shows enhanced fulfillment info
- **✅ Display**: Shows extracted text patterns for debugging
- **✅ Format**: Clear icons and formatting for seller/shipment info

## Current Search Strategy (Maintained)

### UPC Search Strategy ✅
- **Strategy 1**: UPC/barcode search (highest precision)
- **Strategy 2**: Amazon title + brand search (`<title> <brand>`)
- **Strategy 3**: Brand only search (fallback)
- **Strategy 4**: Base search term (final fallback)

### UPC Cleaning ✅
- **Special Character Removal**: Automatically strips characters like `‎`
- **Validation**: Ensures cleaned UPC is numeric and proper length (10-14 digits)
- **Example**: `‎199414326476` → `199414326476`

## Implementation Details

### Seller/Shipment Extraction Sources
- **Primary**: `fulfillment_text`, `seller_info`, `shipping_info`
- **Secondary**: `pricing.seller_info`, `details.seller_info`
- **Fallback**: `raw_html`, `description` if available

### Regex Pattern Examples
```
"Sold by MilleLoom and Shipped by Amazon" →
  - seller_name: "MilleLoom"
  - shipped_by: "Amazon"
  - shipment_type: "Shipped by Amazon"

"Ships from and sold by Amazon.com" →
  - seller_name: "Amazon.com"
  - shipped_by: "Amazon.com"
  - shipment_type: "Shipped by Amazon"
```

## Files Modified

- ✅ `product_matching_system.py` - Removed sample fallbacks, added seller/shipment extraction
- ✅ `context.md` - Updated to reflect all changes

## What Was Removed

- ❌ `_get_sample_target_products()` - No more local file fallbacks
- ❌ `_load_sample_target_product_details()` - No more sample data loading
- ❌ `allow_sample_fallback` parameter - All fallback logic removed
- ❌ All references to "sample data", "demonstration", "pre-downloaded products"

## What Was Added

- ✅ Enhanced regex-based seller/shipment extraction
- ✅ Intelligent Amazon vs Seller shipment detection
- ✅ Clean seller name processing
- ✅ Enhanced reporting with seller/shipment details
- ✅ Live-only Target.com search (no fallbacks)

## System Behavior Now

1. **Amazon Product**: Extracts title, brand, UPC from Amazon product data
2. **Target Search**: Uses UPC first, then title+brand, then brand, then base term
3. **Live Search Only**: Only searches Target.com live - no local files
4. **Seller Extraction**: Uses regex to find "Sold by * and Shipped by *" patterns
5. **Shipment Logic**: Amazon = "Shipped by Amazon", Others = "Shipped by Seller"
6. **Enhanced Reports**: Shows all seller/shipment information clearly