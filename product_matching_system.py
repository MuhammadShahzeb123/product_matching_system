#!/usr/bin/env python3
"""
Comprehensive Product Matching System

This system performs the following improved workflow:
1. Search both Amazon and Target simultaneously using the same search term
2. Fetch detailed product information from both platforms
3. Compare ALL Amazon products with ALL Target products using sophisticated scoring
4. Generate comprehensive matching reports with all possible combinations

The system now provides true cross-platform matching by searching both sites
with the same keywords (e.g., "gaming chair" on both Amazon and Target),
then finding the best matches between all products found.

Usage: python product_matching_system.py "search_term" [--max-results 5]

Example:
python product_matching_system.py "gaming chair" --max-results 3
This will search for "gaming chair" on both Amazon and Target, fetch details
for up to 3 products from each platform, and compare all 9 possible combinations.
"""

import os
import sys
import json
import time
import argparse
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check for curl_cffi availability (used by scrapers)
try:
    import curl_cffi.requests as cf_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    print("⚠️  curl_cffi not available. Some scraping features may be limited.")

# Import existing modules
from amazon_complete_fetcher_parser import AmazonProductExtractor
from target_complete_fetcher_parser import TargetProductExtractor

# Import new Target search scraper module
from target_search_scraper import TargetSearchScraper

# Try to import Amazon search capabilities
try:
    from unneeded.realtime_amazon_extractor import RealTimeAmazonExtractor
    AMAZON_SEARCH_AVAILABLE = True
except ImportError:
    RealTimeAmazonExtractor = None
    AMAZON_SEARCH_AVAILABLE = False
    print("⚠️  Amazon search module not available. Will work with ASIN only.")


@dataclass
class MatchingResult:
    """Data class for product matching results"""
    amazon_product: Dict[str, Any]
    target_product: Dict[str, Any]
    match_score: float
    score_breakdown: Dict[str, Any]
    confidence: str
    timestamp: datetime


class ProxyConfig:
    """Centralized proxy configuration"""
    DEFAULT_PROXY = "http://250621Ev04e-resi_region-US_California:5PjDM1IoS0JSr2c@ca.proxy-jet.io:1010"

    # Alternative proxy configs for fallback
    ALTERNATIVE_PROXIES = [
        "http://250621Ev04e-resi_region-US:5PjDM1IoS0JSr2c@usa.proxy-jet.io:1010",
        "http://250621Ev04e-resi_region-US_New_York:5PjDM1IoS0JSr2c@ny.proxy-jet.io:1010"
    ]

    @staticmethod
    def get_proxy_config() -> Dict[str, str]:
        """Get proxy configuration for requests"""
        return {
            "http": ProxyConfig.DEFAULT_PROXY,
            "https": ProxyConfig.DEFAULT_PROXY
        }

    @staticmethod
    def get_fallback_proxies() -> List[str]:
        """Get list of fallback proxies"""
        return ProxyConfig.ALTERNATIVE_PROXIES


class ProductMatchingScorer:
    """
    Sophisticated product matching scorer with weighted attributes.

    Scoring System:
    - UPC/GTIN/EAN Match: 100 points (Perfect identifier match)
    - Model Number Match: 80 points (High confidence)
    - Brand Match: 40 points (Essential for product identification)
    - Title Similarity (>90%): 70 points
    - Title Similarity (>70%): 50 points
    - Title Similarity (>50%): 30 points
    - Dimensions Match (exact): 60 points
    - Dimensions Match (±5%): 40 points
    - Weight Match (exact): 50 points
    - Weight Match (±10%): 30 points
    - Price Match (±20%): 25 points
    - Category Match: 20 points
    - Color Match: 15 points
    - Material Match: 15 points
    - Feature Keywords Match: 1-10 points per keyword
    """

    def __init__(self):
        self.scoring_weights = {
            'upc_match': 100,
            'model_match': 80,
            'brand_match': 40,
            'title_similarity_high': 70,  # >90%
            'title_similarity_medium': 50,  # >70%
            'title_similarity_low': 30,  # >50%
            'dimensions_exact': 60,
            'dimensions_close': 40,  # ±5%
            'weight_exact': 50,
            'weight_close': 30,  # ±10%
            'price_match': 25,  # ±20%
            'category_match': 20,
            'color_match': 15,
            'material_match': 15,
            'feature_keyword': 5  # per matching keyword
        }

    def calculate_match_score(self, amazon_product: Dict, target_product: Dict) -> Tuple[float, Dict]:
        """
        Calculate comprehensive matching score between Amazon and Target products.

        Returns:
            Tuple of (total_score, score_breakdown)
        """
        score_breakdown = {}
        total_score = 0.0

        # 1. UPC/GTIN/EAN Match (Highest Priority)
        upc_score = self._check_upc_match(amazon_product, target_product)
        if upc_score > 0:
            total_score += upc_score
            score_breakdown['upc_match'] = upc_score

        # 2. Model Number Match
        model_score = self._check_model_match(amazon_product, target_product)
        if model_score > 0:
            total_score += model_score
            score_breakdown['model_match'] = model_score

        # 3. Brand Match
        brand_score = self._check_brand_match(amazon_product, target_product)
        if brand_score > 0:
            total_score += brand_score
            score_breakdown['brand_match'] = brand_score

        # 4. Title Similarity
        title_score = self._check_title_similarity(amazon_product, target_product)
        if title_score > 0:
            total_score += title_score
            score_breakdown['title_similarity'] = title_score

        # 5. Physical Dimensions
        dimension_score = self._check_dimensions_match(amazon_product, target_product)
        if dimension_score > 0:
            total_score += dimension_score
            score_breakdown['dimensions_match'] = dimension_score

        # 6. Weight Match
        weight_score = self._check_weight_match(amazon_product, target_product)
        if weight_score > 0:
            total_score += weight_score
            score_breakdown['weight_match'] = weight_score

        # 7. Price Comparison
        price_score = self._check_price_match(amazon_product, target_product)
        if price_score > 0:
            total_score += price_score
            score_breakdown['price_match'] = price_score

        # 8. Category Match - REMOVED per user request (not effective for accurate matching)
        # category_score = self._check_category_match(amazon_product, target_product)
        # if category_score > 0:
        #     total_score += category_score
        #     score_breakdown['category_match'] = category_score

        # 9. Color Match
        color_score = self._check_color_match(amazon_product, target_product)
        if color_score > 0:
            total_score += color_score
            score_breakdown['color_match'] = color_score

        # 10. Material Match
        material_score = self._check_material_match(amazon_product, target_product)
        if material_score > 0:
            total_score += material_score
            score_breakdown['material_match'] = material_score

        # 11. Feature Keywords Match
        feature_score = self._check_feature_keywords(amazon_product, target_product)
        if feature_score > 0:
            total_score += feature_score
            score_breakdown['feature_keywords'] = feature_score

        # 12. Product Type Compatibility Bonus (Universal - works for any product category)
        product_compatibility = self._check_furniture_compatibility(amazon_product, target_product)
        if product_compatibility > 0:
            total_score += product_compatibility
            score_breakdown['product_compatibility'] = product_compatibility

        return total_score, score_breakdown

    def _extract_text_safely(self, product: Dict, keys: List[str]) -> str:
        """Safely extract text from nested product data"""
        text = ""
        for key_path in keys:
            try:
                keys_list = key_path.split('.')
                value = product
                for k in keys_list:
                    if isinstance(value, dict):
                        value = value.get(k, "")
                    else:
                        value = ""
                        break
                if value and isinstance(value, str):
                    text += f" {value}"
            except:
                continue
        return text.strip().lower()

    def _check_upc_match(self, amazon: Dict, target: Dict) -> float:
        """Check UPC/GTIN/EAN match"""
        amazon_upc = self._extract_text_safely(amazon, [
            'specifications.upc', 'specifications.gtin', 'specifications.ean',
            'identifiers.upc', 'identifiers.gtin', 'identifiers.ean',
            'basic_info.upc', 'basic_info.gtin'
        ])

        target_upc = self._extract_text_safely(target, [
            'basic_info.upc', 'basic_info.gtin',
            'technical_specs.specifications.upc',
            'product_details.upc'
        ])

        if amazon_upc and target_upc and len(amazon_upc) > 8:
            if amazon_upc == target_upc:
                return self.scoring_weights['upc_match']

        return 0

    def _check_model_match(self, amazon: Dict, target: Dict) -> float:
        """Check model number match"""
        amazon_model = self._extract_text_safely(amazon, [
            'specifications.model_number', 'specifications.model',
            'identifiers.model_number', 'basic_info.model_number'
        ])

        target_model = self._extract_text_safely(target, [
            'basic_info.model_number', 'technical_specs.specifications.model_number',
            'product_details.model'
        ])

        if amazon_model and target_model and len(amazon_model) > 3:
            # Exact match
            if amazon_model == target_model:
                return self.scoring_weights['model_match']
            # Partial match (model contained in each other)
            elif amazon_model in target_model or target_model in amazon_model:
                return self.scoring_weights['model_match'] * 0.7

        return 0

    def _check_brand_match(self, amazon: Dict, target: Dict) -> float:
        """Check brand match"""
        amazon_brand = self._extract_text_safely(amazon, ['brand', 'basic_info.brand'])
        target_brand = self._extract_text_safely(target, ['basic_info.brand', 'brand'])

        if amazon_brand and target_brand:
            if amazon_brand == target_brand:
                return self.scoring_weights['brand_match']
            # Similar brands (common abbreviations/variations)
            elif self._brands_similar(amazon_brand, target_brand):
                return self.scoring_weights['brand_match'] * 0.8

        return 0

    def _brands_similar(self, brand1: str, brand2: str) -> bool:
        """Check if brands are similar variations - works across all product categories"""
        brand_mappings = {
            # Tech brands
            'amazon basics': ['amazonbasics', 'amazon', 'basics'],
            'apple': ['apple inc', 'apple computer'],
            'samsung': ['samsung electronics', 'samsung group'],
            'google': ['google llc', 'alphabet'],
            'microsoft': ['microsoft corporation', 'msft'],
            'sony': ['sony corporation', 'sony group'],
            'lg': ['lg electronics', 'lg corp'],
            'hp': ['hewlett-packard', 'hewlett packard'],
            'dell': ['dell technologies', 'dell inc'],
            'lenovo': ['lenovo group'],

            # Furniture brands
            'best office': ['bestoffice'],
            'ikea': ['ikea group'],
            'wayfair': ['wayfair llc'],

            # Fashion brands
            'nike': ['nike inc'],
            'adidas': ['adidas ag'],
            'under armour': ['underarmour'],

            # Home brands
            'cuisinart': ['conair cuisinart'],
            'kitchenaid': ['kitchen aid'],
            'black decker': ['black & decker', 'blackdecker'],

            # Generic variations
            'pro': ['professional'],
            'max': ['maximum'],
            'ultra': ['ultra-'],
            'plus': ['+']
        }

        b1, b2 = brand1.lower().strip(), brand2.lower().strip()

        # Direct match
        if b1 == b2:
            return True

        # Check mapped variations
        for canonical, variations in brand_mappings.items():
            if (b1 == canonical or b1 in variations) and (b2 == canonical or b2 in variations):
                return True

        # Check if one brand contains the other (common with variations)
        if len(b1) > 3 and len(b2) > 3:
            if b1 in b2 or b2 in b1:
                return True

        # Check for common abbreviations (first letters)
        if len(b1.split()) > 1 and len(b2) <= 4:
            abbreviation = ''.join([word[0] for word in b1.split()])
            if abbreviation == b2:
                return True

        if len(b2.split()) > 1 and len(b1) <= 4:
            abbreviation = ''.join([word[0] for word in b2.split()])
            if abbreviation == b1:
                return True

        return False

    def _check_title_similarity(self, amazon: Dict, target: Dict) -> float:
        """Check title similarity using advanced text comparison"""
        amazon_title = self._extract_text_safely(amazon, ['title', 'basic_info.name'])
        target_title = self._extract_text_safely(target, ['basic_info.name', 'title'])

        if not amazon_title or not target_title:
            return 0

        # Clean and normalize titles
        amazon_clean = self._normalize_title(amazon_title)
        target_clean = self._normalize_title(target_title)

        # Calculate similarity using multiple methods
        similarity = self._calculate_text_similarity(amazon_clean, target_clean)

        # Extract key product words from both titles
        amazon_words = set(amazon_clean.lower().split())
        target_words = set(target_clean.lower().split())

        # Bonus for having common important words (any product type)
        common_important_words = amazon_words.intersection(target_words)
        important_word_bonus = min(len(common_important_words) * 0.1, 0.3)  # Up to 30% bonus

        similarity += important_word_bonus

        # More lenient thresholds for all product types
        if similarity >= 0.75:
            return self.scoring_weights['title_similarity_high']
        elif similarity >= 0.5:
            return self.scoring_weights['title_similarity_medium']
        elif similarity >= 0.25:
            return self.scoring_weights['title_similarity_low']
        elif similarity >= 0.1:
            return self.scoring_weights['title_similarity_low'] * 0.5  # Partial match

        return 0

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison - works for any product type"""
        # Remove common noise words and normalize
        noise_words = ['for', 'with', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'of', 'to', 'from']

        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())

        # Remove extra spaces
        normalized = ' '.join(normalized.split())

        # Keep meaningful words (length > 2) and filter out noise words
        # But preserve important descriptive words regardless of category
        words = []
        for w in normalized.split():
            if len(w) > 2 and w not in noise_words:
                words.append(w)

        return ' '.join(words)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using token-based approach"""
        if not text1 or not text2:
            return 0.0

        # Tokenize
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())

        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _check_dimensions_match(self, amazon: Dict, target: Dict) -> float:
        """Check physical dimensions match"""
        amazon_dims = self._extract_dimensions(amazon)
        target_dims = self._extract_dimensions(target)

        if not amazon_dims or not target_dims:
            return 0

        # Compare dimensions with tolerance
        if self._dimensions_match(amazon_dims, target_dims, tolerance=0.0):
            return self.scoring_weights['dimensions_exact']
        elif self._dimensions_match(amazon_dims, target_dims, tolerance=0.05):
            return self.scoring_weights['dimensions_close']

        return 0

    def _extract_dimensions(self, product: Dict) -> Optional[Dict[str, float]]:
        """Extract dimensions from product data"""
        try:
            # Try multiple paths for dimensions
            dim_paths = [
                'physical_attributes',
                'specifications.dimensions',
                'technical_specs.specifications'
            ]

            for path in dim_paths:
                dims_data = self._get_nested_value(product, path)
                if dims_data:
                    extracted = {}
                    # Look for length, width, height
                    for key in ['length', 'width', 'height']:
                        if key in dims_data:
                            try:
                                extracted[key] = float(dims_data[key])
                            except:
                                continue

                    if len(extracted) >= 2:  # At least 2 dimensions
                        return extracted

            return None
        except:
            return None

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return value
        except:
            return None

    def _dimensions_match(self, dims1: Dict, dims2: Dict, tolerance: float = 0.05) -> bool:
        """Check if dimensions match within tolerance"""
        common_keys = set(dims1.keys()).intersection(set(dims2.keys()))
        if len(common_keys) < 2:
            return False

        for key in common_keys:
            val1, val2 = dims1[key], dims2[key]
            if val1 == 0 or val2 == 0:
                continue

            diff = abs(val1 - val2) / max(val1, val2)
            if diff > tolerance:
                return False

        return True

    def _check_weight_match(self, amazon: Dict, target: Dict) -> float:
        """Check weight match"""
        amazon_weight = self._extract_weight(amazon)
        target_weight = self._extract_weight(target)

        if not amazon_weight or not target_weight:
            return 0

        diff = abs(amazon_weight - target_weight) / max(amazon_weight, target_weight)

        if diff == 0:
            return self.scoring_weights['weight_exact']
        elif diff <= 0.1:  # ±10%
            return self.scoring_weights['weight_close']

        return 0

    def _extract_weight(self, product: Dict) -> Optional[float]:
        """Extract weight from product data"""
        try:
            weight_paths = [
                'physical_attributes.weight',
                'specifications.weight',
                'technical_specs.specifications.weight'
            ]

            for path in weight_paths:
                weight_data = self._get_nested_value(product, path)
                if weight_data:
                    try:
                        return float(weight_data)
                    except:
                        continue

            return None
        except:
            return None

    def _check_price_match(self, amazon: Dict, target: Dict) -> float:
        """Check price match within tolerance"""
        amazon_price = self._extract_price(amazon)
        target_price = self._extract_price(target)

        if not amazon_price or not target_price:
            return 0

        diff = abs(amazon_price - target_price) / max(amazon_price, target_price)

        if diff <= 0.2:  # ±20%
            return self.scoring_weights['price_match']

        return 0

    def _extract_price(self, product: Dict) -> Optional[float]:
        """Extract price from product data"""
        try:
            price_paths = [
                'pricing.current_price',
                'pricing.formatted_current_price',
                'pricing.price'
            ]

            for path in price_paths:
                price_data = self._get_nested_value(product, path)
                if price_data:
                    # Extract numeric value from price string
                    price_str = str(price_data)
                    price_match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                    if price_match:
                        return float(price_match.group())

            return None
        except:
            return None

    def _check_category_match(self, amazon: Dict, target: Dict) -> float:
        """Check category match - universal approach for any product type"""
        amazon_cats = self._extract_categories(amazon)
        target_cats = self._extract_categories(target)

        # Method 1: Direct category overlap
        if amazon_cats and target_cats:
            common_categories = amazon_cats.intersection(target_cats)
            if common_categories:
                return self.scoring_weights['category_match']

        # Method 2: Semantic category analysis from titles (universal)
        amazon_title = self._extract_text_safely(amazon, ['title', 'basic_info.name']).lower()
        target_title = self._extract_text_safely(target, ['basic_info.name', 'title']).lower()

        # Extract potential product types from titles
        amazon_product_type = self._extract_product_type_keywords(amazon_title)
        target_product_type = self._extract_product_type_keywords(target_title)

        # Check for common product type indicators
        if amazon_product_type and target_product_type:
            common_types = amazon_product_type.intersection(target_product_type)
            if common_types:
                return self.scoring_weights['category_match']

            # Check for related product types
            related_score = self._check_related_product_types(amazon_product_type, target_product_type)
            if related_score > 0:
                return related_score

        return 0

    def _extract_product_type_keywords(self, title: str) -> set:
        """Extract product type keywords from title - works for any category"""
        # Common product type indicators across all categories
        type_keywords = set()

        # Split title into words
        words = title.lower().split()

        # Look for nouns that typically indicate product types
        # This is more generic than hard-coding specific categories
        potential_types = []

        for i, word in enumerate(words):
            # Skip very short words and numbers
            if len(word) <= 2 or word.isdigit():
                continue

            # Common product type patterns
            if (i == 0 or  # First word is often the product type
                word in ['chair', 'table', 'phone', 'laptop', 'book', 'speaker', 'headphone',
                        'mouse', 'keyboard', 'monitor', 'tablet', 'camera', 'watch', 'bag',
                        'case', 'cable', 'charger', 'stand', 'holder', 'rack', 'shelf',
                        'light', 'lamp', 'fan', 'heater', 'cooler', 'bottle', 'cup', 'mug',
                        'tool', 'drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'kit',
                        'game', 'controller', 'console', 'tv', 'remote', 'adapter']):
                type_keywords.add(word)

            # Look for compound product types (e.g., "office chair", "gaming mouse")
            if i < len(words) - 1:
                compound = f"{word} {words[i+1]}"
                if any(base in compound for base in ['office', 'gaming', 'wireless', 'bluetooth',
                                                   'smart', 'digital', 'electric', 'manual',
                                                   'portable', 'desktop', 'mobile']):
                    type_keywords.add(compound)

        return type_keywords

    def _check_related_product_types(self, amazon_types: set, target_types: set) -> float:
        """Check if product types are related - partial category match"""
        # Define some universal relationships between product types
        related_groups = [
            {'chair', 'seat', 'stool', 'bench'},
            {'table', 'desk', 'workstation', 'stand'},
            {'phone', 'smartphone', 'mobile', 'cell phone'},
            {'laptop', 'notebook', 'computer', 'pc'},
            {'headphone', 'headset', 'earphone', 'earbuds'},
            {'speaker', 'soundbar', 'audio', 'sound system'},
            {'mouse', 'trackball', 'touchpad', 'pointing device'},
            {'keyboard', 'keypad', 'input device'},
            {'monitor', 'display', 'screen', 'lcd', 'led'},
            {'tablet', 'ipad', 'android tablet', 'slate'},
            {'camera', 'webcam', 'camcorder', 'video camera'},
            {'watch', 'smartwatch', 'fitness tracker', 'wearable'},
            {'bag', 'backpack', 'case', 'pouch', 'sleeve'},
            {'cable', 'cord', 'wire', 'connector'},
            {'charger', 'adapter', 'power supply', 'battery'},
            {'light', 'lamp', 'led', 'bulb', 'lighting'},
            {'tool', 'equipment', 'instrument', 'device'}
        ]

        # Check if types belong to the same related group
        for group in related_groups:
            amazon_in_group = any(any(amazon_type in group_item or group_item in amazon_type
                                    for group_item in group) for amazon_type in amazon_types)
            target_in_group = any(any(target_type in group_item or group_item in target_type
                                    for group_item in group) for target_type in target_types)

            if amazon_in_group and target_in_group:
                return self.scoring_weights['category_match'] * 0.7  # Partial match

        return 0

    def _extract_categories(self, product: Dict) -> set:
        """Extract categories from product data"""
        try:
            category_paths = [
                'categories',
                'category_info.category_name',
                'breadcrumbs'
            ]

            categories = set()
            for path in category_paths:
                cat_data = self._get_nested_value(product, path)
                if cat_data:
                    if isinstance(cat_data, list):
                        categories.update([str(c).lower() for c in cat_data])
                    else:
                        categories.add(str(cat_data).lower())

            return categories
        except:
            return set()

    def _check_color_match(self, amazon: Dict, target: Dict) -> float:
        """Check color match"""
        amazon_color = self._extract_color(amazon)
        target_color = self._extract_color(target)

        if amazon_color and target_color and amazon_color == target_color:
            return self.scoring_weights['color_match']

        return 0

    def _extract_color(self, product: Dict) -> Optional[str]:
        """Extract color from product data"""
        try:
            color_paths = [
                'variations.color',
                'specifications.color',
                'product_details.color'
            ]

            for path in color_paths:
                color_data = self._get_nested_value(product, path)
                if color_data:
                    return str(color_data).lower()

            return None
        except:
            return None

    def _check_material_match(self, amazon: Dict, target: Dict) -> float:
        """Check material match"""
        amazon_materials = self._extract_materials(amazon)
        target_materials = self._extract_materials(target)

        if amazon_materials and target_materials:
            common_materials = amazon_materials.intersection(target_materials)
            if common_materials:
                return self.scoring_weights['material_match']

        return 0

    def _extract_materials(self, product: Dict) -> set:
        """Extract materials from product data"""
        try:
            material_paths = [
                'specifications.material',
                'product_details.materials',
                'technical_specs.specifications.material'
            ]

            materials = set()
            for path in material_paths:
                mat_data = self._get_nested_value(product, path)
                if mat_data:
                    if isinstance(mat_data, list):
                        materials.update([str(m).lower() for m in mat_data])
                    else:
                        materials.add(str(mat_data).lower())

            return materials
        except:
            return set()

    def _check_feature_keywords(self, amazon: Dict, target: Dict) -> float:
        """Check feature keywords match"""
        amazon_features = self._extract_features(amazon)
        target_features = self._extract_features(target)

        if not amazon_features or not target_features:
            return 0

        common_features = amazon_features.intersection(target_features)
        return len(common_features) * self.scoring_weights['feature_keyword']

    def _extract_features(self, product: Dict) -> set:
        """Extract feature keywords from product data"""
        try:
            feature_paths = [
                'specifications',
                'product_details.highlights',
                'technical_specs.specifications'
            ]

            features = set()
            for path in feature_paths:
                feat_data = self._get_nested_value(product, path)
                if feat_data:
                    if isinstance(feat_data, dict):
                        for k, v in feat_data.items():
                            features.add(str(k).lower())
                            features.add(str(v).lower())
                    elif isinstance(feat_data, list):
                        for item in feat_data:
                            features.add(str(item).lower())

            # Clean and filter meaningful features
            cleaned_features = set()
            for feature in features:
                if len(feature) > 3 and not feature.isdigit():
                    cleaned_features.add(feature)

            return cleaned_features
        except:
            return set()

    def _check_furniture_compatibility(self, amazon: Dict, target: Dict) -> float:
        """Check product type compatibility - universal for any product category"""
        amazon_title = self._extract_text_safely(amazon, ['title', 'basic_info.name']).lower()
        target_title = self._extract_text_safely(target, ['basic_info.name', 'title']).lower()

        # Extract product type indicators from both titles
        amazon_types = self._extract_universal_product_types(amazon_title)
        target_types = self._extract_universal_product_types(target_title)

        if not amazon_types or not target_types:
            return 0

        # Calculate compatibility score based on product type similarity
        compatibility_score = self._calculate_product_type_compatibility(amazon_types, target_types)

        return compatibility_score

    def _extract_universal_product_types(self, title: str) -> set:
        """Extract product types that work for any product category"""
        types = set()
        words = title.lower().split()

        # Primary product categories - much broader than furniture
        primary_types = {
            # Electronics
            'electronics', 'electronic', 'digital', 'smart', 'wireless', 'bluetooth',
            'phone', 'smartphone', 'mobile', 'iphone', 'android', 'cell',
            'laptop', 'computer', 'pc', 'desktop', 'notebook', 'macbook',
            'tablet', 'ipad', 'kindle', 'e-reader',
            'headphone', 'headphones', 'headset', 'earphones', 'earbuds',
            'speaker', 'speakers', 'soundbar', 'audio', 'bluetooth speaker',
            'mouse', 'keyboard', 'monitor', 'display', 'screen',
            'camera', 'webcam', 'gopro', 'camcorder',
            'watch', 'smartwatch', 'fitness', 'tracker', 'fitbit', 'apple watch',
            'charger', 'cable', 'adapter', 'power', 'battery', 'charging',

            # Furniture & Home
            'chair', 'table', 'desk', 'bed', 'sofa', 'couch', 'dresser', 'cabinet',
            'office', 'gaming', 'ergonomic', 'executive', 'task', 'swivel',
            'dining', 'coffee', 'side', 'end', 'nightstand', 'bookshelf',

            # Clothing & Accessories
            'shirt', 'pants', 'dress', 'jacket', 'shoes', 'boots', 'sneakers',
            'bag', 'backpack', 'purse', 'wallet', 'belt', 'hat', 'cap',
            'watch', 'jewelry', 'necklace', 'bracelet', 'ring',

            # Kitchen & Dining
            'kitchen', 'cooking', 'baking', 'dining',
            'pot', 'pan', 'knife', 'spoon', 'fork', 'plate', 'bowl', 'cup', 'mug',
            'blender', 'mixer', 'toaster', 'microwave', 'oven', 'refrigerator',

            # Sports & Outdoors
            'sports', 'fitness', 'outdoor', 'camping', 'hiking', 'running',
            'bike', 'bicycle', 'skateboard', 'scooter',
            'ball', 'basketball', 'football', 'soccer', 'tennis', 'baseball',

            # Tools & Hardware
            'tool', 'tools', 'drill', 'saw', 'hammer', 'screwdriver', 'wrench',
            'kit', 'set', 'toolbox', 'hardware', 'equipment',

            # Books & Media
            'book', 'books', 'novel', 'textbook', 'magazine', 'comic',
            'movie', 'dvd', 'blu-ray', 'cd', 'vinyl', 'record',
            'game', 'games', 'video game', 'board game', 'puzzle',

            # Health & Beauty
            'health', 'beauty', 'skincare', 'makeup', 'cosmetic',
            'shampoo', 'soap', 'lotion', 'cream', 'serum',
            'vitamin', 'supplement', 'medicine', 'first aid',

            # Automotive
            'car', 'auto', 'automotive', 'vehicle', 'truck', 'motorcycle',
            'tire', 'wheel', 'battery', 'oil', 'parts', 'accessory'
        }

        # Look for these types in the title
        for word in words:
            if word in primary_types:
                types.add(word)

        # Look for compound types
        for i in range(len(words) - 1):
            compound = f"{words[i]} {words[i+1]}"
            if compound in primary_types:
                types.add(compound)

        return types

    def _calculate_product_type_compatibility(self, amazon_types: set, target_types: set) -> float:
        """Calculate compatibility between product types - universal scoring"""
        # Direct type matches get highest score
        direct_matches = amazon_types.intersection(target_types)
        if direct_matches:
            return 35.0  # High compatibility for exact type matches

        # Define universal compatibility groups
        compatibility_groups = {
            'electronics': {
                'mobile_devices': {'phone', 'smartphone', 'mobile', 'iphone', 'android', 'cell', 'tablet', 'ipad'},
                'computers': {'laptop', 'computer', 'pc', 'desktop', 'notebook', 'macbook'},
                'audio': {'headphone', 'headphones', 'headset', 'earphones', 'earbuds', 'speaker', 'speakers', 'soundbar', 'audio'},
                'peripherals': {'mouse', 'keyboard', 'monitor', 'display', 'screen'},
                'accessories': {'charger', 'cable', 'adapter', 'power', 'battery', 'charging', 'case'},
                'wearables': {'watch', 'smartwatch', 'fitness', 'tracker', 'fitbit'}
            },
            'furniture': {
                'seating': {'chair', 'sofa', 'couch', 'bench', 'stool', 'seat'},
                'tables': {'table', 'desk', 'dining', 'coffee', 'side', 'end', 'nightstand'},
                'office': {'office', 'desk', 'chair', 'gaming', 'ergonomic', 'executive', 'task'},
                'storage': {'dresser', 'cabinet', 'bookshelf', 'shelf', 'rack'}
            },
            'apparel': {
                'clothing': {'shirt', 'pants', 'dress', 'jacket', 'clothes'},
                'footwear': {'shoes', 'boots', 'sneakers', 'sandals'},
                'accessories': {'bag', 'backpack', 'purse', 'wallet', 'belt', 'hat', 'cap'}
            },
            'kitchen': {
                'cookware': {'pot', 'pan', 'skillet', 'wok'},
                'utensils': {'knife', 'spoon', 'fork', 'spatula'},
                'appliances': {'blender', 'mixer', 'toaster', 'microwave', 'oven'},
                'dinnerware': {'plate', 'bowl', 'cup', 'mug', 'glass'}
            }
        }

        # Check for compatibility within groups
        for main_category, subcategories in compatibility_groups.items():
            amazon_matches = set()
            target_matches = set()

            for subcat, items in subcategories.items():
                if any(item in amazon_types for item in items):
                    amazon_matches.add(subcat)
                if any(item in target_types for item in items):
                    target_matches.add(subcat)

            # Same subcategory = high compatibility
            if amazon_matches.intersection(target_matches):
                return 30.0

            # Same main category = medium compatibility
            if amazon_matches and target_matches:
                return 20.0

        # Fallback: check for any semantic similarity
        semantic_score = self._check_semantic_similarity(amazon_types, target_types)
        return semantic_score

    def _check_semantic_similarity(self, amazon_types: set, target_types: set) -> float:
        """Check for semantic similarity between product types"""
        # Convert sets to strings for comparison
        amazon_str = ' '.join(amazon_types)
        target_str = ' '.join(target_types)

        # Simple word overlap check
        amazon_words = set(amazon_str.split())
        target_words = set(target_str.split())

        if amazon_words and target_words:
            overlap = amazon_words.intersection(target_words)
            if overlap:
                return min(len(overlap) * 5.0, 15.0)  # 5 points per overlapping word, max 15

        return 0

    def get_confidence_level(self, score: float) -> str:
        """Get confidence level based on score"""
        if score >= 120:
            return "Very High"
        elif score >= 80:
            return "High"
        elif score >= 50:
            return "Medium"
        elif score >= 25:
            return "Low"
        elif score >= 10:
            return "Very Low"
        else:
            return "No Match"


class ProductMatchingSystem:
    """Main system orchestrating the entire product matching workflow"""

    def __init__(self, proxy_config: Optional[Dict] = None):
        """Initialize the product matching system"""
        self.proxy_config = proxy_config or {"url": ProxyConfig.DEFAULT_PROXY}

        # Initialize components with search-based pricing enabled for more reliable pricing
        self.amazon_extractor = AmazonProductExtractor(use_search_pricing=True)
        self.target_extractor = TargetProductExtractor()
        self.scorer = ProductMatchingScorer()

        # Initialize search modules if available
        if AMAZON_SEARCH_AVAILABLE and RealTimeAmazonExtractor is not None:
            self.amazon_searcher = RealTimeAmazonExtractor(self.proxy_config)

        # Initialize new Target search scraper
        self.target_scraper = TargetSearchScraper(proxy_config=self.proxy_config)

        # Results storage
        self.results_dir = Path("matching_results")
        self.results_dir.mkdir(exist_ok=True)

    def _build_amazon_url(self, asin: str) -> str:
        """Build Amazon product URL from ASIN"""
        if not asin:
            return ""
        return f"https://www.amazon.com/dp/{asin}/"

    def _build_target_url(self, tcin: str) -> str:
        """Build Target product URL from TCIN"""
        if not tcin:
            return ""
        return f"https://www.target.com/p/-/A-{tcin}"

    def _extract_amazon_marketplace_info(self, amazon_product: Dict) -> Dict[str, Any]:
        """Extract marketplace information from Amazon product data"""
        marketplace_info = {}

        # Sales rank information
        sales_rank = amazon_product.get('sales_rank', {})
        if sales_rank and sales_rank.get('sales_ranks'):
            primary_rank_info = sales_rank['sales_ranks'][0] if sales_rank['sales_ranks'] else {}
            marketplace_info['sales_rank'] = {
                'primary_rank': primary_rank_info.get('rank'),
                'primary_category': primary_rank_info.get('category', ''),
                'all_ranks': sales_rank.get('sales_ranks', [])
            }

        # Pack size information
        pack_size = amazon_product.get('pack_size', {})
        if pack_size:
            marketplace_info['pack_size'] = {
                'size': pack_size.get('pack_size', 1),
                'description': pack_size.get('pack_description', '')
            }

        # Fulfillment information (from fulfillment_info section)
        fulfillment_info = amazon_product.get('fulfillment_info', {})
        if fulfillment_info:
            marketplace_info['fulfillment'] = {
                'type': fulfillment_info.get('fulfillment_type', 'Unknown'),
                'sold_by': fulfillment_info.get('sold_by', ''),
                'ships_from': fulfillment_info.get('ships_from', ''),
                'is_prime': fulfillment_info.get('is_prime', False)
            }

        # Enhanced seller and shipment extraction using regex patterns
        enhanced_fulfillment = self._extract_enhanced_seller_shipment_info(amazon_product)
        if enhanced_fulfillment:
            marketplace_info['enhanced_fulfillment'] = enhanced_fulfillment

        # Pricing details with search-enhanced pricing support
        pricing = amazon_product.get('pricing', {})
        if pricing:
            # Enhanced pricing structure with search-based pricing
            marketplace_info['pricing'] = {
                'buybox_price': pricing.get('current_price', ''),
                'search_current_price': pricing.get('search_current_price', pricing.get('formatted_current_price', '')),
                'list_price': pricing.get('list_price', ''),
                'search_list_price': pricing.get('search_list_price', ''),
                'was_price': pricing.get('was_price', ''),
                'deal_price': pricing.get('deal_price', ''),
                'discount': pricing.get('discount', ''),
                'more_buying_choices': pricing.get('more_buying_choices', {}),
                'coupon_info': pricing.get('coupon_info', ''),
                'price_comparison': {
                    'detail_page_price': pricing.get('current_price', ''),
                    'search_results_price': pricing.get('search_current_price', pricing.get('formatted_current_price', '')),
                    'price_source': 'search_enhanced' if pricing.get('search_current_price') else 'detail_page'
                }
            }

        return marketplace_info

    def _extract_enhanced_seller_shipment_info(self, amazon_product: Dict) -> Dict[str, Any]:
        """
        Extract enhanced seller and shipment information using regex patterns
        Patterns like 'Sold by * and Shipped by *'
        """

        enhanced_info = {
            'seller_name': '',
            'shipped_by': '',
            'shipment_type': '',
            'extracted_patterns': []
        }

        # Multiple possible sources of seller/shipment text - convert all to strings safely
        text_sources = []

        # List of paths to check for seller/shipment info
        source_paths = [
            ('fulfillment_text', amazon_product.get('fulfillment_text', '')),
            ('seller_info', amazon_product.get('seller_info', '')),
            ('shipping_info', amazon_product.get('shipping_info', '')),
            ('delivery_info', amazon_product.get('delivery_info', '')),
            ('marketplace_info', amazon_product.get('marketplace_info', '')),
            # Check within pricing section for seller info
            ('pricing.seller_info', amazon_product.get('pricing', {}).get('seller_info', '')),
            ('pricing.fulfillment_text', amazon_product.get('pricing', {}).get('fulfillment_text', '')),
            # Check within details/specifications
            ('details.seller_info', amazon_product.get('details', {}).get('seller_info', '')),
            ('specifications.seller_info', amazon_product.get('specifications', {}).get('seller_info', '')),
        ]

        # Also check in raw HTML or description if available
        if 'raw_html' in amazon_product:
            source_paths.append(('raw_html', amazon_product.get('raw_html', '')))
        if 'description' in amazon_product:
            source_paths.append(('description', amazon_product.get('description', '')))

        # Convert all sources to strings safely
        for source_name, source_value in source_paths:
            try:
                if source_value is not None:
                    # Convert to string, handling dicts, lists, etc.
                    if isinstance(source_value, (dict, list)):
                        text_str = str(source_value)
                    else:
                        text_str = str(source_value).strip()

                    # Only add non-empty meaningful text
                    if text_str and text_str not in ['{}', '[]', 'None', 'null']:
                        text_sources.append(text_str)
            except Exception as e:
                # Skip problematic sources
                continue

        # Alternative patterns
        patterns = [
            # "Sold by X and Shipped by Y"
            r'[Ss]old\s+by\s+([^,\n\r]+?)\s+and\s+[Ss]hipped\s+by\s+([^,\n\r\.]+)',
            # "Ships from and sold by X"
            r'[Ss]hips\s+from\s+and\s+sold\s+by\s+([^,\n\r\.]+)',
            # "Sold by X"
            r'[Ss]old\s+by\s+([^,\n\r\.]+)',
            # "Shipped by X"
            r'[Ss]hipped\s+by\s+([^,\n\r\.]+)',
            # "Ships from X"
            r'[Ss]hips\s+from\s+([^,\n\r\.]+)',
        ]

        for text in text_sources:
            # Text is already converted to string and validated
            if not text or len(text.strip()) == 0:
                continue

            # Skip obvious non-useful text
            clean_text = text.strip().lower()
            if clean_text in ['none', 'null', '{}', '[]', '""', "''", 'undefined']:
                continue

            for i, pattern in enumerate(patterns):
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    if i == 0:  # Main pattern: "Sold by X and Shipped by Y"
                        seller = match.group(1).strip()
                        shipper = match.group(2).strip()

                        enhanced_info['seller_name'] = seller
                        enhanced_info['shipped_by'] = shipper

                        # Determine shipment type
                        if 'amazon' in shipper.lower():
                            enhanced_info['shipment_type'] = 'Shipped by Amazon'
                        else:
                            enhanced_info['shipment_type'] = 'Shipped by Seller'

                        enhanced_info['extracted_patterns'].append({
                            'pattern': 'sold_by_and_shipped_by',
                            'text': match.group(0),
                            'seller': seller,
                            'shipper': shipper
                        })

                    elif i == 1:  # "Ships from and sold by X"
                        seller = match.group(1).strip()
                        enhanced_info['seller_name'] = seller
                        enhanced_info['shipped_by'] = seller  # Same entity

                        if 'amazon' in seller.lower():
                            enhanced_info['shipment_type'] = 'Shipped by Amazon'
                        else:
                            enhanced_info['shipment_type'] = 'Shipped by Seller'

                        enhanced_info['extracted_patterns'].append({
                            'pattern': 'ships_from_and_sold_by',
                            'text': match.group(0),
                            'seller': seller,
                            'shipper': seller
                        })

                    elif i == 2:  # "Sold by X"
                        seller = match.group(1).strip()
                        if not enhanced_info['seller_name']:  # Don't override if already found
                            enhanced_info['seller_name'] = seller

                        enhanced_info['extracted_patterns'].append({
                            'pattern': 'sold_by',
                            'text': match.group(0),
                            'seller': seller
                        })

                    elif i == 3:  # "Shipped by X"
                        shipper = match.group(1).strip()
                        if not enhanced_info['shipped_by']:  # Don't override if already found
                            enhanced_info['shipped_by'] = shipper

                            if 'amazon' in shipper.lower():
                                enhanced_info['shipment_type'] = 'Shipped by Amazon'
                            else:
                                enhanced_info['shipment_type'] = 'Shipped by Seller'

                        enhanced_info['extracted_patterns'].append({
                            'pattern': 'shipped_by',
                            'text': match.group(0),
                            'shipper': shipper
                        })

                    elif i == 4:  # "Ships from X"
                        shipper = match.group(1).strip()
                        if not enhanced_info['shipped_by']:  # Don't override if already found
                            enhanced_info['shipped_by'] = shipper

                            if 'amazon' in shipper.lower():
                                enhanced_info['shipment_type'] = 'Shipped by Amazon'
                            else:
                                enhanced_info['shipment_type'] = 'Shipped by Seller'

                        enhanced_info['extracted_patterns'].append({
                            'pattern': 'ships_from',
                            'text': match.group(0),
                            'shipper': shipper
                        })

        # Clean up extracted names
        if enhanced_info['seller_name']:
            enhanced_info['seller_name'] = self._clean_seller_name(enhanced_info['seller_name'])
        if enhanced_info['shipped_by']:
            enhanced_info['shipped_by'] = self._clean_seller_name(enhanced_info['shipped_by'])

        # If we still don't have shipment type but have shipped_by, determine it
        if not enhanced_info['shipment_type'] and enhanced_info['shipped_by']:
            if 'amazon' in enhanced_info['shipped_by'].lower():
                enhanced_info['shipment_type'] = 'Shipped by Amazon'
            else:
                enhanced_info['shipment_type'] = 'Shipped by Seller'

        return enhanced_info

    def _clean_seller_name(self, name: str) -> str:
        """Clean up seller/shipper names by removing common artifacts"""
        if not name:
            return name

        # Remove common HTML artifacts and extra spaces
        name = re.sub(r'<[^>]+>', '', name)  # Remove HTML tags
        name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
        name = name.strip()

        # Remove common trailing artifacts
        name = re.sub(r'\s*[\.\,\;\:]$', '', name)  # Remove trailing punctuation
        name = re.sub(r'\s*\([^)]*\)$', '', name)   # Remove trailing parentheses content

        return name.strip()

    def _extract_amazon_price(self, product: Dict) -> str:
        """Extract price from Amazon product data with multiple fallbacks, prioritizing search-based pricing"""
        # Prioritize search-based pricing paths first (more reliable)
        search_price_paths = [
            'pricing.search_current_price',
            'pricing.formatted_current_price'
        ]

        # Try search-based pricing first
        for path in search_price_paths:
            try:
                keys = path.split('.')
                value = product
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                if value:
                    # Clean and format price
                    price_str = str(value).strip()
                    if price_str and price_str != "0" and price_str.lower() != "none":
                        # Add $ if not present
                        if not price_str.startswith('$') and price_str.replace('.', '').replace(',', '').isdigit():
                            price_str = f"${price_str}"
                        return f"{price_str} (search-enhanced)"
            except:
                continue

        # Fallback to traditional pricing paths
        fallback_price_paths = [
            'pricing.current_price',
            'price.current',
            'price',
            'formatted_price',
            'current_price'
        ]

        for path in fallback_price_paths:
            try:
                keys = path.split('.')
                value = product
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                if value:
                    # Clean and format price
                    price_str = str(value).strip()
                    if price_str and price_str != "0" and price_str.lower() != "none":
                        # Add $ if not present
                        if not price_str.startswith('$') and price_str.replace('.', '').replace(',', '').isdigit():
                            price_str = f"${price_str}"
                        return price_str
            except:
                continue

        return ""

    def _extract_target_price(self, product: Dict) -> str:
        """Extract price from Target product data with multiple fallbacks"""
        price_paths = [
            'pricing.formatted_current_price',
            'pricing.current_price',
            'basic_info.price',
            'price.current',
            'price',
            'formatted_price',
            'current_price'
        ]

        for path in price_paths:
            try:
                keys = path.split('.')
                value = product
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                if value:
                    # Clean and format price
                    price_str = str(value).strip()
                    if price_str and price_str != "0" and price_str.lower() != "none":
                        # Add $ if not present
                        if not price_str.startswith('$') and price_str.replace('.', '').replace(',', '').isdigit():
                            price_str = f"${price_str}"
                        return price_str
            except:
                continue

        return ""

    def _search_target_products_intelligently(self, amazon_product: Dict, base_search_term: str = "", max_results: int = 5) -> List[Dict]:
        """
        Search Target products using intelligent queries based on Amazon product data.

        Args:
            amazon_product: Amazon product data to use for creating search queries
            base_search_term: Original search term (e.g., "gaming chair")
            max_results: Maximum number of results to return

        Returns:
            List of Target product dictionaries
        """
        print(f"🧠 Using intelligent Target search based on Amazon product data...")

        # Use the new Target scraper module's intelligent search
        try:
            products = self.target_scraper.intelligent_search(
                amazon_product, 
                base_search_term, 
                max_results, 
                save_results=False
            )
            
            if products:
                print(f"✅ Intelligent search found {len(products)} Target products")
            else:
                print("❌ No products found with intelligent search")
                
            return products
            
        except Exception as e:
            print(f"❌ Error in intelligent Target search: {str(e)}")
            return []

    def run_complete_matching_workflow(self, search_term: str, max_results: int = 5) -> List[MatchingResult]:
        """
        Run the complete product matching workflow.

        Args:
            search_term: Search term for products (used on both Amazon and Target)
            max_results: Maximum number of products to fetch from each platform

        Returns:
            List of MatchingResult objects with all possible combinations
        """
        print(f"🚀 Starting product matching workflow for: '{search_term}'")
        print("=" * 60)

        # Step 1: Search both Amazon and Target simultaneously with the same term
        print("� Step 1: Searching both Amazon and Target...")

        # Search Amazon
        print("   📦 Searching Amazon...")
        amazon_products = self._search_amazon_products(search_term, max_results)

        if not amazon_products:
            print("❌ No Amazon products found.")
            return []

        print(f"   ✅ Found {len(amazon_products)} Amazon product(s)")

        # Search Target
        print("   🎯 Searching Target...")
        target_products = self._search_target_products(search_term, max_results)

        if not target_products:
            print("❌ No Target products found.")
            return []

        print(f"   ✅ Found {len(target_products)} Target product(s)")

        # Step 2: Fetch detailed information for all products
        print(f"\n📊 Step 2: Fetching detailed product information...")

        # Get detailed Amazon product info
        detailed_amazon_products = []
        for i, product in enumerate(amazon_products, 1):
            asin = product.get('asin')
            if not asin:
                continue

            print(f"   📦 Fetching Amazon product details {i}/{len(amazon_products)}...")
            detailed_product = self.amazon_extractor.extract_product(asin)

            if detailed_product and 'error' not in detailed_product:
                detailed_amazon_products.append(detailed_product)

            time.sleep(1)  # Rate limiting

        # Get detailed Target product info
        detailed_target_products = []
        for i, product in enumerate(target_products, 1):
            product_url = product.get('product_url')
            if not product_url:
                continue

            print(f"   🎯 Fetching Target product details {i}/{len(target_products)}...")
            detailed_product = self._fetch_target_product_details(product_url)

            if detailed_product and 'error' not in detailed_product:
                detailed_target_products.append(detailed_product)

            time.sleep(2)  # Rate limiting

        print(f"✅ Fetched details for {len(detailed_amazon_products)} Amazon and {len(detailed_target_products)} Target products")

        # Step 3: Compare ALL Amazon products with ALL Target products
        print(f"\n🔬 Step 3: Comparing products (Total comparisons: {len(detailed_amazon_products)} × {len(detailed_target_products)} = {len(detailed_amazon_products) * len(detailed_target_products)})...")
        matching_results = []

        for i, amazon_product in enumerate(detailed_amazon_products, 1):
            amazon_title = amazon_product.get('title', 'Unknown')[:50]

            for j, target_product in enumerate(detailed_target_products, 1):
                target_title = target_product.get('basic_info', {}).get('name', 'Unknown')[:50]

                print(f"   ⚖️  Comparing Amazon #{i} vs Target #{j}...")
                print(f"      Amazon: {amazon_title}...")
                print(f"      Target: {target_title}...")

                score, score_breakdown = self.scorer.calculate_match_score(
                    amazon_product, target_product
                )

                confidence = self.scorer.get_confidence_level(score)

                matching_result = MatchingResult(
                    amazon_product=amazon_product,
                    target_product=target_product,
                    match_score=score,
                    score_breakdown=score_breakdown,
                    confidence=confidence,
                    timestamp=datetime.now()
                )

                matching_results.append(matching_result)

                print(f"      📊 Match Score: {score:.1f} ({confidence} confidence)")
                print()

        # Step 4: Sort by score and generate report
        matching_results.sort(key=lambda x: x.match_score, reverse=True)

        print("📈 Step 4: Generating matching report...")
        self._generate_matching_report(search_term, matching_results)

        print(f"\n🎉 Workflow completed! Found {len(matching_results)} product comparisons.")
        print(f"🏆 Best match score: {matching_results[0].match_score:.1f} ({matching_results[0].confidence})")

        return matching_results

    def run_amazon_url_matching_workflow(self, amazon_url: str, target_search_term: str, max_target_results: int = 5) -> List[MatchingResult]:
        """
        Run product matching workflow with specific Amazon URL against Target search results.

        Args:
            amazon_url: Direct Amazon product URL to scrape
            target_search_term: Search term to use for Target products
            max_target_results: Maximum number of Target products to compare against

        Returns:
            List of MatchingResult objects
        """
        print(f"🚀 Starting Amazon URL matching workflow")
        print(f"📦 Amazon URL: {amazon_url}")
        print(f"🎯 Target search term: '{target_search_term}'")
        print("=" * 80)

        # Step 1: Extract Amazon product from URL
        print("📦 Step 1: Scraping Amazon product from URL...")
        amazon_product = self._scrape_amazon_product_from_url(amazon_url)

        if not amazon_product:
            print("❌ Failed to scrape Amazon product.")
            return []

        product_title = amazon_product.get('title', 'Unknown')[:80]
        print(f"✅ Successfully scraped Amazon product: {product_title}...")

        # Step 2: Search Target with provided search term using intelligent search
        print(f"\n🎯 Step 2: Intelligently searching Target based on Amazon product data...")
        target_products = self._search_target_products_intelligently(amazon_product, target_search_term, max_target_results)

        if not target_products:
            print("❌ No Target products found.")
            return []

        print(f"✅ Found {len(target_products)} live Target product(s)")

        # Step 3: Fetch detailed Target product information
        print(f"\n📊 Step 3: Fetching detailed Target product information...")
        detailed_target_products = []

        for i, product in enumerate(target_products, 1):
            # For live search results, fetch details from Target URL
            product_url = product.get('product_url')
            if not product_url:
                continue

            print(f"   📋 Fetching Target product details {i}/{len(target_products)}...")
            detailed_product = self._fetch_target_product_details(product_url)

            if detailed_product and 'error' not in detailed_product:
                detailed_target_products.append(detailed_product)

            time.sleep(2)  # Rate limiting for live requests

        print(f"✅ Successfully loaded details for {len(detailed_target_products)} Target product(s)")

        if not detailed_target_products:
            print("❌ No detailed Target product data available.")
            return []

        # Step 4: Compare Amazon product with all Target products
        print(f"\n🔬 Step 4: Comparing Amazon product with {len(detailed_target_products)} Target products...")
        matching_results = []

        amazon_title = amazon_product.get('title', 'Unknown')[:50]

        for i, target_product in enumerate(detailed_target_products, 1):
            target_title = target_product.get('basic_info', {}).get('name', 'Unknown')[:50]

            print(f"   ⚖️  Comparing with Target product {i}/{len(detailed_target_products)}...")
            print(f"      Amazon: {amazon_title}...")
            print(f"      Target: {target_title}...")

            score, score_breakdown = self.scorer.calculate_match_score(
                amazon_product, target_product
            )

            confidence = self.scorer.get_confidence_level(score)

            matching_result = MatchingResult(
                amazon_product=amazon_product,
                target_product=target_product,
                match_score=score,
                score_breakdown=score_breakdown,
                confidence=confidence,
                timestamp=datetime.now()
            )

            matching_results.append(matching_result)

            print(f"      📊 Match Score: {score:.1f} ({confidence} confidence)")
            print()

        # Step 5: Sort by score and generate report
        matching_results.sort(key=lambda x: x.match_score, reverse=True)

        print("📈 Step 5: Generating matching report...")
        self._generate_url_matching_report(amazon_url, target_search_term, matching_results)

        print(f"\n🎉 URL matching workflow completed! Found {len(matching_results)} product comparisons.")
        if matching_results:
            print(f"🏆 Best match score: {matching_results[0].match_score:.1f} ({matching_results[0].confidence})")

        return matching_results

    def _scrape_amazon_product_from_url(self, amazon_url: str) -> Optional[Dict]:
        """
        Extract Amazon product information from a given URL.

        Args:
            amazon_url: Full Amazon product URL

        Returns:
            Dict containing product information or None if failed
        """
        try:
            # Extract ASIN from URL
            asin = self._extract_asin_from_url(amazon_url)

            if not asin:
                print(f"❌ Could not extract ASIN from URL: {amazon_url}")
                return None

            print(f"   📋 Extracted ASIN: {asin}")

            # Use existing Amazon extractor
            detailed_product = self.amazon_extractor.extract_product(asin)

            # Better error handling for different response types
            if detailed_product is None:
                print(f"❌ Amazon extractor returned None for ASIN: {asin}")
                return None

            if not isinstance(detailed_product, dict):
                print(f"❌ Amazon extractor returned invalid type: {type(detailed_product)}")
                return None

            if 'error' in detailed_product:
                print(f"❌ Error extracting product: {detailed_product['error']}")
                return None

            return detailed_product

        except Exception as e:
            print(f"❌ Error scraping Amazon URL: {str(e)}")
            return None

    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """
        Extract ASIN from Amazon URL.

        Handles various Amazon URL formats:
        - https://www.amazon.com/dp/B08KTN2NSW/
        - https://www.amazon.com/product-title/dp/B08KTN2NSW/ref=xxx
        - https://amazon.com/gp/product/B08KTN2NSW
        - https://www.amazon.com/s?k=search+term&asin=B08KTN2NSW
        """
        import re

        # Common ASIN patterns in Amazon URLs
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})/?',           # /dp/ASIN/
            r'/gp/product/([A-Z0-9]{10})/?',   # /gp/product/ASIN/
            r'asin=([A-Z0-9]{10})',            # asin=ASIN parameter
            r'/product/([A-Z0-9]{10})/?',      # /product/ASIN/
        ]

        for pattern in asin_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                asin = match.group(1).upper()
                # Validate ASIN format (10 characters, alphanumeric)
                if len(asin) == 10 and asin.isalnum():
                    return asin

        return None

    def _generate_url_matching_report(self, amazon_url: str, target_search_term: str, results: List[MatchingResult]) -> None:
        """Generate comprehensive matching report for URL-based matching"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"url_matching_report_{target_search_term.replace(' ', '_')}_{timestamp}.json"
        filepath = self.results_dir / filename

        # Prepare report data with enhanced pricing information
        amazon_product = results[0].amazon_product if results else {}
        amazon_asin = amazon_product.get('asin', '')
        amazon_price = self._extract_amazon_price(amazon_product)

        # Extract detailed pricing information for the report
        pricing_info = amazon_product.get('pricing', {})
        search_enhancement = amazon_product.get('search_enhancement', {})

        report_data = {
            'matching_type': 'amazon_url_vs_target_search',
            'amazon_url': amazon_url,
            'target_search_term': target_search_term,
            'timestamp': timestamp,
            'total_comparisons': len(results),
            'amazon_product': {
                'title': amazon_product.get('title', ''),
                'asin': amazon_asin,
                'brand': amazon_product.get('brand', ''),
                'price': amazon_price,
                'url': self._build_amazon_url(amazon_asin),
                # Enhanced pricing details with search-based pricing
                'pricing_details': {
                    'detail_page_price': pricing_info.get('current_price', ''),
                    'search_current_price': pricing_info.get('search_current_price', pricing_info.get('formatted_current_price', '')),
                    'list_price': pricing_info.get('list_price', ''),
                    'search_list_price': pricing_info.get('search_list_price', ''),
                    'more_buying_choices': pricing_info.get('more_buying_choices', {}),
                    'coupon_info': pricing_info.get('coupon_info', ''),
                    'was_price': pricing_info.get('was_price', ''),
                    'price_source': 'search_enhanced' if pricing_info.get('search_current_price') else 'detail_page',
                    'search_enhancement_status': search_enhancement.get('pricing_enhanced', False)
                },
                # Marketplace data (already enhanced with search pricing)
                'marketplace_info': self._extract_amazon_marketplace_info(amazon_product)
            },
            'summary': {
                'unique_target_products': len(set(r.target_product.get('basic_info', {}).get('tcin', '') for r in results)),
                'best_match_score': results[0].match_score if results else 0,
                'best_match_confidence': results[0].confidence if results else 'None'
            },
            'comparisons': []
        }

        for i, result in enumerate(results):
            target_product = result.target_product
            target_tcin = target_product.get('basic_info', {}).get('tcin', '')
            target_price = self._extract_target_price(target_product)

            comparison = {
                'rank': i + 1,
                'target_product': {
                    'title': target_product.get('basic_info', {}).get('name', ''),
                    'tcin': target_tcin,
                    'brand': target_product.get('basic_info', {}).get('brand', ''),
                    'price': target_price,
                    'url': self._build_target_url(target_tcin)
                },
                'match_score': result.match_score,
                'confidence': result.confidence,
                'score_breakdown': result.score_breakdown
            }
            report_data['comparisons'].append(comparison)

        # Save report
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📊 URL matching report saved: {filepath}")

        # Print summary
        print("\n📋 URL MATCHING SUMMARY:")
        print(f"   Amazon URL: {amazon_url}")
        print(f"   Target search term: {target_search_term}")
        print(f"   Total comparisons: {len(results)}")
        print(f"   Target products analyzed: {report_data['summary']['unique_target_products']}")

        if results:
            best_match = results[0]
            amazon_product = best_match.amazon_product

            print(f"\n🏆 BEST MATCH:")
            print(f"   Amazon: {amazon_product.get('title', '')[:70]}...")
            print(f"   Target: {best_match.target_product.get('basic_info', {}).get('name', '')[:70]}...")
            print(f"   Score: {best_match.match_score:.1f} ({best_match.confidence})")

            # Show enhanced pricing information
            pricing_details = report_data['amazon_product']['pricing_details']
            print(f"\n💰 SEARCH-ENHANCED PRICING:")

            if pricing_details['search_current_price']:
                print(f"   🔍 Search Current Price: {pricing_details['search_current_price']}")
                if pricing_details['search_list_price']:
                    print(f"   🏷️ Search List Price: {pricing_details['search_list_price']}")

                # Show format you requested
                current = pricing_details['search_current_price']
                list_p = pricing_details['search_list_price']
                if current and list_p:
                    print(f"   📊 Your Format: {current} List: {list_p}")

                more_choices = pricing_details.get('more_buying_choices', {})
                if isinstance(more_choices, dict) and more_choices.get('text'):
                    print(f"   🛒 More Buying Choices: {more_choices['text']}")
                elif more_choices and isinstance(more_choices, str):
                    print(f"   🛒 More Buying Choices: {more_choices}")

            if pricing_details['detail_page_price']:
                print(f"   📄 Detail Page Price: {pricing_details['detail_page_price']}")

            print(f"   📈 Price Source: {pricing_details['price_source']}")
            print(f"   ✅ Search Enhanced: {'Yes' if pricing_details['search_enhancement_status'] else 'No'}")

            # Show enhanced seller and shipment information
            marketplace_info = report_data['amazon_product']['marketplace_info']
            enhanced_fulfillment = marketplace_info.get('enhanced_fulfillment', {})

            if enhanced_fulfillment and any([enhanced_fulfillment.get('seller_name'), enhanced_fulfillment.get('shipped_by')]):
                print(f"\n🚚 SELLER & SHIPMENT INFO:")

                if enhanced_fulfillment.get('seller_name'):
                    print(f"   🏪 Sold by: {enhanced_fulfillment['seller_name']}")

                if enhanced_fulfillment.get('shipped_by'):
                    print(f"   📦 Shipped by: {enhanced_fulfillment['shipped_by']}")

                if enhanced_fulfillment.get('shipment_type'):
                    print(f"   🚛 Shipment type: {enhanced_fulfillment['shipment_type']}")

                # Show extracted patterns for debugging
                patterns = enhanced_fulfillment.get('extracted_patterns', [])
                if patterns:
                    print(f"   🔍 Extracted from text: '{patterns[0].get('text', '')}'")

            print("\n   📊 Score breakdown:")
            for category, score in best_match.score_breakdown.items():
                print(f"     {category}: {score:.1f}")

            # Show top matches if available
            if len(results) > 1:
                print(f"\n🥈 TOP MATCHES:")
                for i, result in enumerate(results[:3], 1):
                    target_title = result.target_product.get('basic_info', {}).get('name', '')[:50]
                    print(f"   {i}. Score: {result.match_score:.1f} | Target: {target_title}...")

    def _search_amazon_products(self, search_term: str, max_results: int = 5) -> List[Dict]:
        """Search Amazon and return list of products with basic info"""
        try:
            if not AMAZON_SEARCH_AVAILABLE:
                print("⚠️  Amazon search not available.")
                return []

            # Search Amazon
            search_results = self.amazon_searcher.search_and_extract(search_term, max_pages=1)
            products = search_results.get('products', [])

            if not products:
                print("   ❌ No products found in Amazon search.")
                return []

            # Return up to max_results products
            return products[:max_results]

        except Exception as e:
            print(f"   ❌ Error in Amazon search: {str(e)}")
            return []

    def _search_target_products(self, search_term: str, max_results: int = 5) -> List[Dict]:
        """Search Target for products using the new Target scraper module"""
        try:
            print(f"🔍 Searching Target for '{search_term}'...")

            # Use the new Target scraper module
            products = self.target_scraper.search_products(search_term, max_results, save_results=False)

            if not products:
                print("   ❌ No products found in Target search.")
                return []

            print(f"   ✅ Found {len(products)} Target products")
            return products

        except Exception as e:
            print(f"   ❌ Target search error: {str(e)}")
            return []

    def _fetch_target_product_details(self, product_url: str) -> Optional[Dict]:
        """Fetch detailed Target product information using the new Target scraper module"""
        try:
            # Use the new Target scraper module for URL scraping
            detailed_product = self.target_scraper.scrape_product_url(product_url, save_results=False)
            return detailed_product
        except Exception as e:
            print(f"❌ Error fetching Target product details: {str(e)}")
            return None

    def _generate_matching_report(self, search_term: str, results: List[MatchingResult]) -> None:
        """Generate comprehensive matching report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matching_report_{search_term.replace(' ', '_')}_{timestamp}.json"
        filepath = self.results_dir / filename

        # Prepare report data
        report_data = {
            'search_term': search_term,
            'timestamp': timestamp,
            'total_comparisons': len(results),
            'summary': {
                'unique_amazon_products': len(set(r.amazon_product.get('asin', '') for r in results)),
                'unique_target_products': len(set(r.target_product.get('basic_info', {}).get('tcin', '') for r in results)),
                'best_match_score': results[0].match_score if results else 0,
                'best_match_confidence': results[0].confidence if results else 'None'
            },
            'comparisons': []
        }

        for i, result in enumerate(results):
            amazon_product = result.amazon_product
            target_product = result.target_product

            amazon_asin = amazon_product.get('asin', '')
            target_tcin = target_product.get('basic_info', {}).get('tcin', '')

            amazon_price = self._extract_amazon_price(amazon_product)
            target_price = self._extract_target_price(target_product)

            comparison = {
                'rank': i + 1,
                'amazon_product': {
                    'title': amazon_product.get('title', ''),
                    'asin': amazon_asin,
                    'brand': amazon_product.get('brand', ''),
                    'price': amazon_price,
                    'url': self._build_amazon_url(amazon_asin),
                    # NEW: Marketplace data
                    'marketplace_info': self._extract_amazon_marketplace_info(amazon_product)
                },
                'target_product': {
                    'title': target_product.get('basic_info', {}).get('name', ''),
                    'tcin': target_tcin,
                    'brand': target_product.get('basic_info', {}).get('brand', ''),
                    'price': target_price,
                    'url': self._build_target_url(target_tcin)
                },
                'match_score': result.match_score,
                'confidence': result.confidence,
                'score_breakdown': result.score_breakdown
            }
            report_data['comparisons'].append(comparison)

        # Save report
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📊 Report saved: {filepath}")

        # Print summary
        print("\n📋 MATCHING SUMMARY:")
        print(f"   Search term: {search_term}")
        print(f"   Total comparisons: {len(results)}")
        print(f"   Unique Amazon products: {report_data['summary']['unique_amazon_products']}")
        print(f"   Unique Target products: {report_data['summary']['unique_target_products']}")

        if results:
            best_match = results[0]
            amazon_marketplace = self._extract_amazon_marketplace_info(best_match.amazon_product)

            print(f"\n🏆 BEST MATCH:")
            print(f"   Amazon: {best_match.amazon_product.get('title', '')[:60]}...")
            print(f"   Target: {best_match.target_product.get('basic_info', {}).get('name', '')[:60]}...")
            print(f"   Score: {best_match.match_score:.1f} ({best_match.confidence})")

            # Display Amazon marketplace information
            if amazon_marketplace:
                print(f"\n📊 AMAZON MARKETPLACE INFO:")

                # Sales rank
                sales_rank = amazon_marketplace.get('sales_rank', {})
                if sales_rank.get('primary_rank'):
                    print(f"   📈 Sales Rank: #{sales_rank['primary_rank']} in {sales_rank.get('primary_category', 'Unknown')}")

                # Fulfillment
                fulfillment = amazon_marketplace.get('fulfillment', {})
                if fulfillment.get('type'):
                    fulfillment_type = fulfillment['type']
                    fulfillment_display = {
                        'AMZ': '🏪 Amazon (AMZ)',
                        'FBA': '📦 Fulfilled by Amazon (FBA)',
                        'FBM': '🚚 Fulfilled by Merchant (FBM)'
                    }.get(fulfillment_type, f"🔍 {fulfillment_type}")
                    print(f"   🚚 Fulfillment: {fulfillment_display}")

                    if fulfillment.get('sold_by'):
                        print(f"   🏪 Sold by: {fulfillment['sold_by']}")

                # Enhanced seller and shipment information
                enhanced_fulfillment = amazon_marketplace.get('enhanced_fulfillment', {})
                if enhanced_fulfillment and any([enhanced_fulfillment.get('seller_name'), enhanced_fulfillment.get('shipped_by')]):
                    print(f"\n🚚 ENHANCED SELLER & SHIPMENT INFO:")

                    if enhanced_fulfillment.get('seller_name'):
                        print(f"   🏪 Sold by: {enhanced_fulfillment['seller_name']}")

                    if enhanced_fulfillment.get('shipped_by'):
                        print(f"   📦 Shipped by: {enhanced_fulfillment['shipped_by']}")

                    if enhanced_fulfillment.get('shipment_type'):
                        print(f"   🚛 Shipment type: {enhanced_fulfillment['shipment_type']}")

                    # Show extracted patterns for debugging
                    patterns = enhanced_fulfillment.get('extracted_patterns', [])
                    if patterns:
                        print(f"   🔍 Extracted from: '{patterns[0].get('text', '')}'")

                # Pack size
                pack_size = amazon_marketplace.get('pack_size', {})
                if pack_size.get('size') and pack_size['size'] > 1:
                    print(f"   📦 Pack Size: {pack_size['size']} units")

                # Pricing details
                pricing = amazon_marketplace.get('pricing', {})
                if pricing.get('buybox_price'):
                    print(f"   💰 Buy Box Price: {pricing['buybox_price']}")
                if pricing.get('list_price') and pricing['list_price'] != pricing.get('buybox_price'):
                    print(f"   💵 List Price: {pricing['list_price']}")
                if pricing.get('discount'):
                    print(f"   💸 Discount: {pricing['discount']}")

            print("\n   📊 Score breakdown:")
            for category, score in best_match.score_breakdown.items():
                print(f"     {category}: {score:.1f}")

            # Show top 3 matches if available
            if len(results) > 1:
                print(f"\n🥈 TOP MATCHES:")
                for i, result in enumerate(results[:5], 1):
                    amazon_title = result.amazon_product.get('title', '')[:40]
                    target_title = result.target_product.get('basic_info', {}).get('name', '')[:40]
                    print(f"   {i}. Score: {result.match_score:.1f} | Amazon: {amazon_title}... | Target: {target_title}...")

        print(f"\n🕐 Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Comprehensive Product Matching System")
    parser.add_argument("search_term", nargs='?', help="Search term for products (used on both Amazon and Target)")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of products to fetch from each platform (default: 5)")
    parser.add_argument("--amazon-url", help="Use specific Amazon product URL instead of searching")
    parser.add_argument("--target-search", help="Target search term to use with --amazon-url")
    parser.add_argument("--asin", help="Use specific Amazon ASIN instead of searching")
    parser.add_argument("--target-urls", nargs="*", help="Specific Target URLs to compare against")

    args = parser.parse_args()

    # Initialize system
    system = ProductMatchingSystem()

    if args.amazon_url:
        # Amazon URL vs Target search mode
        if not args.target_search:
            print("❌ --target-search is required when using --amazon-url")
            print("Example: python product_matching_system.py --amazon-url 'https://amazon.com/dp/B08KTN2NSW' --target-search 'office chair'")
            sys.exit(1)

        print(f"🎯 Amazon URL matching mode")
        results = system.run_amazon_url_matching_workflow(
            args.amazon_url,
            args.target_search,
            max_target_results=args.max_results
        )

        if results:
            print(f"\n🏆 Best match found with score: {results[0].match_score:.1f}")
        else:
            print("\n❌ No matches found.")

    elif args.asin and args.target_urls:
        # Direct comparison mode
        print(f"🎯 Direct comparison mode: ASIN {args.asin} vs {len(args.target_urls)} Target products")
        # Implementation for direct comparison would go here
        print("⚠️  Direct comparison mode not implemented yet. Use search mode.")

    elif args.search_term:
        # Full workflow mode - search both platforms with same term
        results = system.run_complete_matching_workflow(
            args.search_term,
            max_results=args.max_results
        )

        if results:
            print(f"\n🏆 Best match found with score: {results[0].match_score:.1f}")
        else:
            print("\n❌ No matches found.")

    else:
        # Show help if no valid arguments provided
        parser.print_help()
        print("\n💡 USAGE EXAMPLES:")
        print("1. Search both platforms: python product_matching_system.py 'gaming chair'")
        print("2. Amazon URL vs Target: python product_matching_system.py --amazon-url 'https://amazon.com/dp/B08KTN2NSW' --target-search 'office chair'")
        print("3. Interactive mode: python product_matching_system.py (no arguments)")


if __name__ == "__main__":
    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        print("🛒 Product Matching System - Interactive Mode")
        print("=" * 50)
        print("Choose matching mode:")
        print("1. Search both Amazon and Target with same term")
        print("2. Use specific Amazon URL vs Target search")

        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":
            search_term = input("Enter search term: ").strip()
            if not search_term:
                print("❌ No search term provided!")
                sys.exit(1)

            try:
                max_results = int(input("Max products to compare from each platform (default 5): ") or "5")
            except ValueError:
                max_results = 5

            system = ProductMatchingSystem()
            results = system.run_complete_matching_workflow(search_term, max_results)

            if results:
                print(f"\n🎉 Found {len(results)} product comparisons!")
                print(f"🏆 Best match score: {results[0].match_score:.1f}")
            else:
                print("\n😞 No matches found.")

        elif choice == "2":
            amazon_url = input("Enter Amazon product URL: ").strip()
            if not amazon_url:
                print("❌ No Amazon URL provided!")
                sys.exit(1)

            target_search = input("Enter Target search term: ").strip()
            if not target_search:
                print("❌ No Target search term provided!")
                sys.exit(1)

            try:
                max_results = int(input("Max Target products to compare (default 5): ") or "5")
            except ValueError:
                max_results = 5

            system = ProductMatchingSystem()
            results = system.run_amazon_url_matching_workflow(amazon_url, target_search, max_results)

            if results:
                print(f"\n🎉 Found {len(results)} product comparisons!")
                print(f"🏆 Best match score: {results[0].match_score:.1f}")
            else:
                print("\n😞 No matches found.")

        else:
            print("❌ Invalid choice!")
    else:
        main()
