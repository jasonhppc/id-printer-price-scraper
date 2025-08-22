import os
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import json
import logging
import re
from urllib.parse import urljoin, urlparse
from currency_converter import CurrencyConverter
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class EnhancedPrinterScraper:
    def __init__(self):
        self.results = []
        self.currency_converter = CurrencyConverter()
        self.session = requests.Session()
        
        # Enhanced headers with rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Create data directory
        os.makedirs('../data/prices', exist_ok=True)
        
        # Load configurations
        self.load_website_configs()
        self.load_target_printers()
    
    def load_website_configs(self):
        """Load website configurations from JSON file"""
        try:
            with open('website_configs.json', 'r') as f:
                config = json.load(f)
                self.websites = config.get('websites', {})
                logging.info(f"Loaded {len(self.websites)} website configurations")
        except FileNotFoundError:
            logging.error("website_configs.json not found! Using default config.")
            self.websites = self.get_default_websites()
    
    def load_target_printers(self):
        """Load target printers from config or use defaults"""
        try:
            with open('website_configs.json', 'r') as f:
                config = json.load(f)
                self.target_printers = config.get('target_printers', DEFAULT_PRINTERS)
        except FileNotFoundError:
            self.target_printers = DEFAULT_PRINTERS
    
    def get_default_websites(self):
        """Default website configurations"""
        return {
            "bodno.com": {
                "name": "Bodno",
                "base_url": "https://bodno.com",
                "search_url": "https://bodno.com/search?q={query}",
                "currency": "USD",
                "selectors": {
                    "product_container": ".product-item, .grid-product__content",
                    "title": "h3 a, .grid-product__title, .product-title",
                    "price": ".price, .money, .product-price",
                    "link": "h3 a, .grid-product__link"
                },
                "enabled": True
            },
            "officeworks.com.au": {
                "name": "Officeworks Australia",
                "base_url": "https://www.officeworks.com.au",
                "search_url": "https://www.officeworks.com.au/shop/search?q={query}&view=grid&page=1&sortBy=bestmatch",
                "currency": "AUD",
                "selectors": {
                    "product_container": ".search-results-product-item, .product-tile",
                    "title": ".search-results-product-item__name, .product-tile__name",
                    "price": ".search-results-product-item__price, .price",
                    "link": ".search-results-product-item__link, .product-tile__link"
                },
                "enabled": True
            },
            "jbhifi.com.au": {
                "name": "JB Hi-Fi Australia",
                "base_url": "https://www.jbhifi.com.au",
                "search_url": "https://www.jbhifi.com.au/search?page=1&query={query}",
                "currency": "AUD",
                "selectors": {
                    "product_container": ".ek-product-card, .product-item",
                    "title": ".ek-product-card__title, .product-title",
                    "price": ".ek-product-card__price, .price",
                    "link": ".ek-product-card__link, .product-link"
                },
                "enabled": True
            }
        }
    
    def get_headers(self):
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,en-AU;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        # Handle comma as thousands separator
        if ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator if dot comes after
            if cleaned.rfind(',') < cleaned.rfind('.'):
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Check if comma is decimal separator (European style)
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def safe_request(self, url, max_retries=3):
        """Make request with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt * random.uniform(1, 2))
                else:
                    logging.error(f"All attempts failed for {url}")
                    return None
    
    def search_website(self, website_key, website_config, printer_model):
        """Search a specific website for printer prices"""
        if not website_config.get('enabled', True):
            return
        
        try:
            # Format search query
            query = printer_model.replace(' ', '+')
            search_url = website_config['search_url'].format(query=query)
            
            logging.info(f"Searching {website_config['name']} for {printer_model}")
            
            response = self.safe_request(search_url)
            if not response:
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            selectors = website_config['selectors']
            
            # Find product containers
            products = soup.select(selectors['product_container'])
            
            found_results = 0
            for product in products[:5]:  # Check first 5 results
                try:
                    # Extract title
                    title_elem = product.select_one(selectors['title'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Check if this product matches our search
                    if not self.is_relevant_product(title, printer_model):
                        continue
                    
                    # Extract price
                    price_elem = product.select_one(selectors['price'])
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.get_text(strip=True)
                    price = self.clean_price(price_text)
                    
                    if not price:
                        continue
                    
                    # Convert currency if needed
                    currency = website_config.get('currency', 'AUD')
                    price_aud = self.currency_converter.convert_to_aud(price, currency)
                    
                    # Extract product link
                    link_elem = product.select_one(selectors.get('link', 'a'))
                    product_url = search_url  # Default to search URL
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        product_url = urljoin(website_config['base_url'], href)
                    
                    # Store result with required columns
                    result = {
                        'model': printer_model,
                        'supplier': website_config['name'],
                        'website': website_key,
                        'title': title,
                        'price_original': price,
                        'currency_original': currency,
                        'price_aud': price_aud,
                        'url': product_url,
                        'search_url': search_url,
                        'scraped_at': datetime.now().isoformat(),
                        'status': 'success'
                    }
                    
                    self.results.append(result)
                    found_results += 1
                    
                    logging.info(f"Found: {title} - ${price_aud:.2f} AUD")
                    
                except Exception as e:
                    logging.warning(f"Error processing product on {website_key}: {e}")
                    continue
            
            if found_results == 0:
                logging.info(f"No relevant products found on {website_config['name']}")
            
            # Respectful delay between requests
            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))
            
        except Exception as e:
            logging.error(f"Error searching {website_key}: {e}")
    
    def is_relevant_product(self, title, printer_model):
        """Check if product title is relevant to our search"""
        title_lower = title.lower()
        model_words = printer_model.lower().split()
        
        # Check if most key words from model name appear in title
        matches = sum(1 for word in model_words if word in title_lower)
        return matches >= len(model_words) * 0.6  # At least 60% of words match
    
    def scrape_all_prices(self):
        """Main scraping method"""
        logging.info("Starting enhanced price scraper...")
        logging.info(f"Exchange rate: 1 USD = {self.currency_converter.get_usd_to_aud_rate():.4f} AUD")
        
        total_searches = len([w for w in self.websites.values() if w.get('enabled', True)]) * len(self.target_printers)
        current_search = 0
        
        for printer in self.target_printers:
            logging.info(f"\n{'='*50}")
            logging.info(f"Searching for: {printer}")
            logging.info(f"{'='*50}")
            
            for website_key, website_config in self.websites.items():
                if website_config.get('enabled', True):
                    current_search += 1
                    logging.info(f"Progress: {current_search}/{total_searches}")
                    self.search_website(website_key, website_config, printer)
        
        return self.results
    
    def extract_brand_from_model(self, model):
        """Extract brand/manufacturer from model name"""
        brand_mapping = {
            'fargo': 'HID Fargo',
            'dtc': 'HID Fargo', 
            'evolis': 'Evolis',
            'zebra': 'Zebra',
            'zc': 'Zebra',
            'magicard': 'Magicard',
            'entrust': 'Entrust',
            'sigma': 'Entrust',
            'badgy': 'Evolis',
            'primacy': 'Evolis',
            'pronto': 'Magicard'
        }
        
        model_lower = model.lower()
        for keyword, brand in brand_mapping.items():
            if keyword in model_lower:
                return brand
        
        # Default fallback - use first word
        return model.split()[0].title()

    def format_output_data(self):
        """Format results into the required table structure"""
        formatted_results = []
        
        for result in self.results:
            # Extract brand from model
            brand = self.extract_brand_from_model(result['model'])
            
            # Determine country from website
            country = 'Australia' if any(tld in result['website'] for tld in ['.au', 'australia']) else 'United States'
            
            formatted_result = {
                'brand': brand,
                'manufacturer': brand,  # Same as brand for these products
                'model': result['model'],
                'price': f"${result['price_aud']:.2f} AUD",
                'supplier': result['supplier'],
                'link': result['url'],
                'country': country,
                'scraped_date': result['scraped_at'][:10],  # Just the date part
                'original_price': f"${result['price_original']:.2f} {result['currency_original']}" if result.get('price_original') else None
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results

    def save_results(self):
        """Save results in the required format with specified columns"""
        if not self.results:
            logging.warning("No results to save")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Format data with required columns
        formatted_data = self.format_output_data()
        
        # Create DataFrame with specific column order
        columns = ['brand', 'manufacturer', 'model', 'price', 'supplier', 'link', 'country', 'scraped_date', 'original_price']
        df = pd.DataFrame(formatted_data)[columns]
        
        # Sort by brand, then model, then price
        df = df.sort_values(['brand', 'model', 'price'])
        
        # Save timestamped files
        csv_path = f'../data/prices/prices_{timestamp}.csv'
        json_path = f'../data/prices/prices_{timestamp}.json'
        
        # Save CSV with clean formatting
        df.to_csv(csv_path, index=False)
        
        # Save JSON with clean structure
        json_output = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_results': len(formatted_data),
            'currency': 'AUD',
            'data': formatted_data
        }
        
        with open(json_path, 'w') as f:
            json.dump(json_output, f, indent=2)
        
        # Save latest results in both formats
        df.to_csv('../data/prices/latest_prices.csv', index=False)
        
        with open('../data/prices/latest_prices.json', 'w') as f:
            json.dump(json_output, f, indent=2)
        
        # Generate summary
        self.generate_summary(df)
        
        logging.info(f"Results saved to {csv_path}")
        return csv_path
    
    def generate_summary(self, df):
        """Generate and save summary statistics"""
        summary = {
            'scrape_time': datetime.now().isoformat(),
            'total_results': len(df),
            'unique_models': df['model'].nunique(),
            'unique_suppliers': df['supplier'].nunique(),
            'price_stats': {
                'min_price': float(df['price_aud'].min()),
                'max_price': float(df['price_aud'].max()),
                'avg_price': float(df['price_aud'].mean()),
                'median_price': float(df['price_aud'].median())
            },
            'by_model': {}
        }
        
        # Per-model statistics
        for model in df['model'].unique():
            model_df = df[df['model'] == model]
            summary['by_model'][model] = {
                'count': len(model_df),
                'min_price': float(model_df['price_aud'].min()),
                'max_price': float(model_df['price_aud'].max()),
                'avg_price': float(model_df['price_aud'].mean()),
                'suppliers': model_df['supplier'].tolist()
            }
        
        # Save summary
        with open('../data/prices/latest_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logging.info("Summary statistics generated")

if __name__ == "__main__":
    scraper = EnhancedPrinterScraper()
    results = scraper.scrape_all_prices()
    
    if results:
        csv_file = scraper.save_results()
        logging.info(f"Scraping completed successfully. {len(results)} results found.")
        
        # Print formatted table for GitHub Actions logs
        df = pd.DataFrame(self.format_output_data())
        print("\n" + "="*80)
        print("PRICE COMPARISON TABLE")
        print("="*80)
        
        # Display table with required columns only
        display_columns = ['brand', 'model', 'price', 'supplier', 'country']
        if not df.empty:
            print(df[display_columns].to_string(index=False, max_colwidth=30))
        
        print(f"\nTotal results: {len(results)}")
        print(f"Unique brands: {df['brand'].nunique() if not df.empty else 0}")
        print(f"Unique models: {df['model'].nunique() if not df.empty else 0}")
        print(f"Suppliers checked: {df['supplier'].nunique() if not df.empty else 0}")
        
        # Show best deals by model
        if not df.empty:
            print("\nBEST DEALS BY MODEL:")
            print("-" * 50)
            for model in df['model'].unique():
                model_df = df[df['model'] == model].sort_values('price')
                if not model_df.empty:
                    best = model_df.iloc[0]
                    print(f"{best['brand']} {model}: {best['price']} at {best['supplier']} ({best['country']})")
        
        sys.exit(0)
    else:
        logging.error("No results found!")
        sys.exit(1)
