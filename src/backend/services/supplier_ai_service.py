"""
Supplier-specific AI service for document analysis and price extraction
Extends the existing AI service with supplier-focused capabilities
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger
import base64
import io

class SupplierAIService:
    """
    AI service specialized for supplier document analysis and price extraction
    """
    
    def __init__(self):
        self._initialize_patterns()
        self._initialize_categories()
        
    def _initialize_patterns(self):
        """Initialize regex patterns for supplier document analysis"""
        
        # Price patterns - various formats
        self.price_patterns = [
            # €24.50, € 24,50, EUR 24.50
            re.compile(r'(?:€\s*|EUR\s*|Euro\s*)(\d{1,6}(?:[.,]\d{2})?)', re.IGNORECASE),
            # 24.50€, 24,50 €, 24.50 EUR
            re.compile(r'(\d{1,6}(?:[.,]\d{2})?)\s*(?:€|EUR|Euro)', re.IGNORECASE),
            # $24.50, USD 24.50
            re.compile(r'(?:\$\s*|USD\s*)(\d{1,6}(?:[.,]\d{2})?)', re.IGNORECASE),
            # Price: 24.50, Preis: 24,50
            re.compile(r'(?:price|preis|cost|kosten)[\s:]*(\d{1,6}(?:[.,]\d{2})?)', re.IGNORECASE),
        ]
        
        # Quantity patterns
        self.quantity_patterns = [
            # 10kg, 5 kg, 100 pieces
            re.compile(r'(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|pcs?|pieces?|stück|stk)', re.IGNORECASE),
            # per kg, je kg, pro Stück
            re.compile(r'(?:per|je|pro)\s*(kg|g|l|ml|pcs?|pieces?|stück|stk)', re.IGNORECASE),
        ]
        
        # Product name patterns
        self.product_patterns = [
            # Article number patterns
            re.compile(r'(?:art\.?[-\s]*nr\.?|artikel[-\s]*nr\.?|item[-\s]*no\.?)[\s:]*([A-Z0-9-]+)', re.IGNORECASE),
            # Product description patterns
            re.compile(r'(?:produkt|product|artikel|item)[\s:]*([A-Za-z0-9\s,-]+)', re.IGNORECASE),
        ]
        
        # Supplier info patterns
        self.supplier_patterns = [
            # VAT/Tax ID
            re.compile(r'(?:ust\.?[-\s]*id\.?|vat[-\s]*id|tax[-\s]*id)[\s:]*([A-Z]{2}\d{9,12})', re.IGNORECASE),
            # Contact patterns
            re.compile(r'(?:tel\.?|phone|telefon)[\s:]*([+\d\s()-]+)', re.IGNORECASE),
            re.compile(r'(?:fax)[\s:]*([+\d\s()-]+)', re.IGNORECASE),
            re.compile(r'(?:email|e-mail)[\s:]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
        ]
        
        # Date patterns
        self.date_patterns = [
            # DD.MM.YYYY, DD/MM/YYYY
            re.compile(r'(\d{1,2}[./]\d{1,2}[./]\d{4})', re.IGNORECASE),
            # YYYY-MM-DD
            re.compile(r'(\d{4}-\d{1,2}-\d{1,2})', re.IGNORECASE),
            # Valid until, gültig bis
            re.compile(r'(?:valid until|gültig bis|expires?)[\s:]*(\d{1,2}[./]\d{1,2}[./]\d{4})', re.IGNORECASE),
        ]
        
        # Delivery terms patterns
        self.delivery_patterns = [
            re.compile(r'(?:delivery|lieferung|versand)[\s:]*(\d+)[\s]*(?:days?|tage?|werktage?)', re.IGNORECASE),
            re.compile(r'(?:lead time|lieferzeit)[\s:]*(\d+)[\s]*(?:days?|tage?)', re.IGNORECASE),
        ]
        
        # Payment terms patterns
        self.payment_patterns = [
            re.compile(r'(?:payment|zahlung)[\s:]*(\d+)[\s]*(?:days?|tage?)[\s]*(?:net|netto)', re.IGNORECASE),
            re.compile(r'(\d+)[\s]*(?:days?|tage?)[\s]*(?:net|netto)', re.IGNORECASE),
        ]
        
    def _initialize_categories(self):
        """Initialize product categories and keywords"""
        self.category_keywords = {
            'beverages': [
                'kaffee', 'coffee', 'tee', 'tea', 'wasser', 'water', 'saft', 'juice',
                'bier', 'beer', 'wein', 'wine', 'cola', 'limonade', 'getränk'
            ],
            'dairy': [
                'milch', 'milk', 'käse', 'cheese', 'butter', 'joghurt', 'yogurt',
                'sahne', 'cream', 'quark', 'molkerei'
            ],
            'meat': [
                'fleisch', 'meat', 'rind', 'beef', 'schwein', 'pork', 'huhn', 'chicken',
                'lamm', 'lamb', 'wurst', 'sausage', 'schinken', 'ham'
            ],
            'fish': [
                'fisch', 'fish', 'lachs', 'salmon', 'thunfisch', 'tuna', 'garnele',
                'shrimp', 'muschel', 'seafood', 'meeresfrüchte'
            ],
            'vegetables': [
                'gemüse', 'vegetable', 'salat', 'lettuce', 'tomate', 'tomato',
                'kartoffel', 'potato', 'zwiebel', 'onion', 'karotte', 'carrot'
            ],
            'fruits': [
                'obst', 'fruit', 'apfel', 'apple', 'banane', 'banana', 'orange',
                'zitrone', 'lemon', 'beere', 'berry', 'traube', 'grape'
            ],
            'grains': [
                'getreide', 'grain', 'reis', 'rice', 'nudel', 'pasta', 'brot', 'bread',
                'mehl', 'flour', 'hafer', 'oat', 'weizen', 'wheat'
            ],
            'frozen': [
                'tiefkühl', 'frozen', 'gefrier', 'eis', 'ice cream', 'tk'
            ],
            'cleaning': [
                'reinigung', 'cleaning', 'spülmittel', 'detergent', 'seife', 'soap',
                'desinfekt', 'disinfect', 'putzen', 'hygiene'
            ],
            'office': [
                'büro', 'office', 'papier', 'paper', 'stift', 'pen', 'ordner',
                'folder', 'drucker', 'printer', 'tinte', 'ink'
            ]
        }
        
    def analyze_document(self, document_text: str, document_type: str = 'unknown') -> Dict[str, Any]:
        """
        Analyze a supplier document and extract structured information
        
        Args:
            document_text: Raw text content of the document
            document_type: Type of document (price_list, invoice, contract, etc.)
            
        Returns:
            Structured analysis results
        """
        logger.info(f"Analyzing {document_type} document ({len(document_text)} characters)")
        
        analysis = {
            'document_type': document_type,
            'extracted_at': datetime.now().isoformat(),
            'text_length': len(document_text),
            'supplier_info': self._extract_supplier_info(document_text),
            'products': self._extract_products(document_text),
            'prices': self._extract_prices(document_text),
            'dates': self._extract_dates(document_text),
            'terms': self._extract_terms(document_text),
            'categories': self._categorize_content(document_text),
            'quality_score': 0.0,
            'validation_errors': []
        }
        
        # Calculate quality score
        analysis['quality_score'] = self._calculate_quality_score(analysis)
        
        # Validate extracted data
        analysis['validation_errors'] = self._validate_extracted_data(analysis)
        
        logger.info(f"Document analysis completed. Quality score: {analysis['quality_score']:.2f}")
        
        return analysis
    
    def _extract_supplier_info(self, text: str) -> Dict[str, Any]:
        """Extract supplier information from document"""
        supplier_info = {
            'tax_id': None,
            'contact_phone': None,
            'contact_fax': None,
            'contact_email': None,
            'address_lines': []
        }
        
        # Extract tax ID
        for pattern in self.supplier_patterns:
            matches = pattern.findall(text)
            if matches and 'tax' in pattern.pattern.lower():
                supplier_info['tax_id'] = matches[0]
                break
        
        # Extract contact information
        for pattern in self.supplier_patterns:
            matches = pattern.findall(text)
            if matches:
                if 'tel' in pattern.pattern.lower() or 'phone' in pattern.pattern.lower():
                    supplier_info['contact_phone'] = matches[0]
                elif 'fax' in pattern.pattern.lower():
                    supplier_info['contact_fax'] = matches[0]
                elif 'email' in pattern.pattern.lower():
                    supplier_info['contact_email'] = matches[0]
        
        return supplier_info
    
    def _extract_products(self, text: str) -> List[Dict[str, Any]]:
        """Extract product information from document"""
        products = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) < 10:  # Skip very short lines
                continue
                
            # Look for lines that might contain product information
            # Heuristic: lines with both text and numbers, potential prices
            if re.search(r'[a-zA-Z].*\d', line) and len(line.split()) >= 2:
                product = {
                    'line_number': line_num + 1,
                    'raw_text': line,
                    'extracted_name': self._extract_product_name(line),
                    'extracted_price': self._extract_price_from_line(line),
                    'extracted_quantity': self._extract_quantity_from_line(line),
                    'category': self._categorize_product(line)
                }
                
                # Only add if we found meaningful information
                if product['extracted_name'] or product['extracted_price']:
                    products.append(product)
        
        return products[:50]  # Limit to 50 products to avoid overwhelming
    
    def _extract_prices(self, text: str) -> List[Dict[str, Any]]:
        """Extract all price information from document"""
        prices = []
        
        for pattern in self.price_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                price_str = match.group(1).replace(',', '.')
                try:
                    price_value = float(price_str)
                    prices.append({
                        'value': price_value,
                        'currency': self._extract_currency(match.group(0)),
                        'context': text[max(0, match.start()-50):match.end()+50].strip(),
                        'position': match.start()
                    })
                except ValueError:
                    continue
        
        # Remove duplicates and sort by position
        unique_prices = []
        seen_values = set()
        for price in sorted(prices, key=lambda x: x['position']):
            price_key = (price['value'], price['currency'])
            if price_key not in seen_values:
                unique_prices.append(price)
                seen_values.add(price_key)
        
        return unique_prices[:20]  # Limit to 20 prices
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract date information from document"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                date_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                try:
                    # Try to parse the date
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates.append({
                            'raw_date': date_str,
                            'parsed_date': parsed_date.isoformat(),
                            'context': text[max(0, match.start()-30):match.end()+30].strip(),
                            'type': self._classify_date_type(match.group(0))
                        })
                except:
                    continue
        
        return dates
    
    def _extract_terms(self, text: str) -> Dict[str, Any]:
        """Extract business terms (delivery, payment, etc.)"""
        terms = {
            'delivery_days': None,
            'payment_days': None,
            'minimum_order': None,
            'discount_tiers': []
        }
        
        # Extract delivery terms
        for pattern in self.delivery_patterns:
            matches = pattern.findall(text)
            if matches:
                try:
                    terms['delivery_days'] = int(matches[0])
                    break
                except ValueError:
                    continue
        
        # Extract payment terms
        for pattern in self.payment_patterns:
            matches = pattern.findall(text)
            if matches:
                try:
                    terms['payment_days'] = int(matches[0])
                    break
                except ValueError:
                    continue
        
        return terms
    
    def _categorize_content(self, text: str) -> List[str]:
        """Categorize document content based on keywords"""
        text_lower = text.lower()
        found_categories = []
        
        for category, keywords in self.category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_categories.append(category)
        
        return found_categories
    
    def _extract_product_name(self, line: str) -> Optional[str]:
        """Extract product name from a text line"""
        # Remove common noise patterns
        cleaned = re.sub(r'^\d+\.?\s*', '', line)  # Remove line numbers
        cleaned = re.sub(r'\s+\d+[.,]\d{2}\s*€?\s*$', '', cleaned)  # Remove trailing prices
        cleaned = re.sub(r'\s+\d+\s*(?:kg|g|l|ml|pcs?|stück)\s*$', '', cleaned, flags=re.IGNORECASE)  # Remove quantities
        
        # Extract meaningful product name
        if len(cleaned.strip()) >= 3:
            return cleaned.strip()
        
        return None
    
    def _extract_price_from_line(self, line: str) -> Optional[float]:
        """Extract price from a single line"""
        for pattern in self.price_patterns:
            matches = pattern.findall(line)
            if matches:
                try:
                    price_str = matches[0].replace(',', '.')
                    return float(price_str)
                except ValueError:
                    continue
        return None
    
    def _extract_quantity_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract quantity information from a line"""
        for pattern in self.quantity_patterns:
            matches = pattern.findall(line)
            if matches:
                if len(matches[0]) == 2:  # (number, unit)
                    try:
                        value = float(matches[0][0].replace(',', '.'))
                        unit = matches[0][1].lower()
                        return {'value': value, 'unit': unit}
                    except ValueError:
                        continue
        return None
    
    def _categorize_product(self, line: str) -> Optional[str]:
        """Categorize a product based on its description"""
        line_lower = line.lower()
        
        for category, keywords in self.category_keywords.items():
            if any(keyword in line_lower for keyword in keywords):
                return category
        
        return None
    
    def _extract_currency(self, price_text: str) -> str:
        """Extract currency from price text"""
        if '€' in price_text or 'eur' in price_text.lower():
            return 'EUR'
        elif '$' in price_text or 'usd' in price_text.lower():
            return 'USD'
        else:
            return 'EUR'  # Default assumption
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        formats = [
            '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%d.%m.%y', '%d/%m/%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    def _classify_date_type(self, context: str) -> str:
        """Classify the type of date based on context"""
        context_lower = context.lower()
        if any(word in context_lower for word in ['valid', 'gültig', 'expires']):
            return 'expiry'
        elif any(word in context_lower for word in ['created', 'erstellt', 'datum']):
            return 'created'
        elif any(word in context_lower for word in ['delivery', 'lieferung']):
            return 'delivery'
        else:
            return 'unknown'
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate quality score for the analysis"""
        score = 0.0
        max_score = 100.0
        
        # Points for extracted data
        if analysis['supplier_info']['tax_id']:
            score += 15
        if analysis['supplier_info']['contact_email']:
            score += 10
        if analysis['supplier_info']['contact_phone']:
            score += 10
        
        # Points for products found
        if analysis['products']:
            score += min(len(analysis['products']) * 2, 20)
        
        # Points for prices found
        if analysis['prices']:
            score += min(len(analysis['prices']) * 1.5, 15)
        
        # Points for dates found
        if analysis['dates']:
            score += min(len(analysis['dates']) * 3, 15)
        
        # Points for business terms
        if analysis['terms']['delivery_days']:
            score += 5
        if analysis['terms']['payment_days']:
            score += 5
        
        # Points for categorization
        if analysis['categories']:
            score += min(len(analysis['categories']) * 2, 10)
        
        return min(score, max_score)
    
    def _validate_extracted_data(self, analysis: Dict[str, Any]) -> List[str]:
        """Validate extracted data and return list of issues"""
        errors = []
        
        # Validate prices
        for price in analysis['prices']:
            if price['value'] <= 0:
                errors.append(f"Invalid price value: {price['value']}")
            if price['value'] > 10000:  # Suspiciously high price
                errors.append(f"Suspiciously high price: {price['value']}")
        
        # Validate products
        for product in analysis['products']:
            if not product['extracted_name'] and not product['extracted_price']:
                errors.append(f"Product on line {product['line_number']} has no meaningful data")
        
        # Validate supplier info
        if analysis['supplier_info']['tax_id']:
            tax_id = analysis['supplier_info']['tax_id']
            if not re.match(r'^[A-Z]{2}\d{9,12}$', tax_id):
                errors.append(f"Invalid tax ID format: {tax_id}")
        
        return errors
    
    def create_price_list_from_analysis(self, analysis: Dict[str, Any], supplier_id: int) -> List[Dict[str, Any]]:
        """
        Create structured price list entries from document analysis
        
        Args:
            analysis: Document analysis results
            supplier_id: ID of the supplier
            
        Returns:
            List of price list entries ready for database insertion
        """
        price_entries = []
        
        for product in analysis['products']:
            if product['extracted_name'] and product['extracted_price']:
                entry = {
                    'supplier_id': supplier_id,
                    'product_name': product['extracted_name'],
                    'price': product['extracted_price'],
                    'currency': 'EUR',  # Default, could be improved
                    'category': product['category'],
                    'specifications': {
                        'extracted_from_line': product['line_number'],
                        'raw_text': product['raw_text'],
                        'analysis_quality': analysis['quality_score']
                    }
                }
                
                # Add quantity information if available
                if product['extracted_quantity']:
                    entry['unit'] = product['extracted_quantity']['unit']
                    entry['specifications']['unit_quantity'] = product['extracted_quantity']['value']
                
                # Add validity dates if found
                expiry_dates = [d for d in analysis['dates'] if d['type'] == 'expiry']
                if expiry_dates:
                    entry['valid_until'] = expiry_dates[0]['parsed_date']
                
                price_entries.append(entry)
        
        return price_entries
    
    def extract_supplier_contact_updates(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract potential updates for supplier contact information"""
        updates = {}
        
        supplier_info = analysis['supplier_info']
        
        if supplier_info['contact_email']:
            updates['email'] = supplier_info['contact_email']
        
        if supplier_info['contact_phone']:
            updates['phone'] = supplier_info['contact_phone']
        
        if supplier_info['tax_id']:
            updates['tax_id'] = supplier_info['tax_id']
        
        if analysis['terms']['payment_days']:
            updates['payment_terms'] = f"{analysis['terms']['payment_days']} Tage netto"
        
        return updates

# Create service instance
supplier_ai_service = SupplierAIService()