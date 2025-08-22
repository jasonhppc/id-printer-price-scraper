import requests
import logging
from datetime import datetime, timedelta
import json
import os

class CurrencyConverter:
    def __init__(self):
        self.cache_file = '../data/exchange_rates.json'
        self.cache_duration = timedelta(hours=12)  # Cache for 12 hours
        self.fallback_rate = 1.50  # Fallback USD to AUD rate
        
    def get_usd_to_aud_rate(self):
        """Get current USD to AUD exchange rate with caching"""
        # Try to load from cache first
        cached_rate = self.load_cached_rate()
        if cached_rate:
            return cached_rate
        
        # Fetch fresh rate from multiple sources
        rate = self.fetch_exchange_rate()
        if rate:
            self.cache_rate(rate)
            return rate
        
        # Use fallback rate
        logging.warning(f"Using fallback exchange rate: {self.fallback_rate}")
        return self.fallback_rate
    
    def load_cached_rate(self):
        """Load exchange rate from cache if still valid"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                
                cached_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cached_time < self.cache_duration:
                    logging.info(f"Using cached exchange rate: {data['rate']}")
                    return data['rate']
        except Exception as e:
            logging.warning(f"Error loading cached rate: {e}")
        
        return None
    
    def fetch_exchange_rate(self):
        """Fetch current exchange rate from API"""
        apis = [
            {
                'url': 'https://api.exchangerate-api.com/v4/latest/USD',
                'parser': lambda data: data['rates']['AUD']
            },
            {
                'url': 'https://open.er-api.com/v6/latest/USD',
                'parser': lambda data: data['rates']['AUD']
            },
            {
                'url': 'https://api.fixer.io/latest?base=USD&symbols=AUD',
                'parser': lambda data: data['rates']['AUD']
            }
        ]
        
        for api in apis:
            try:
                response = requests.get(api['url'], timeout=10)
                response.raise_for_status()
                data = response.json()
                rate = api['parser'](data)
                
                if rate and 1.0 < rate < 2.0:  # Sanity check
                    logging.info(f"Fetched exchange rate: 1 USD = {rate} AUD")
                    return rate
                    
            except Exception as e:
                logging.warning(f"Failed to fetch rate from {api['url']}: {e}")
                continue
        
        return None
    
    def cache_rate(self, rate):
        """Cache the exchange rate"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            data = {
                'rate': rate,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Error caching rate: {e}")
    
    def convert_to_aud(self, amount, from_currency):
        """Convert any currency to AUD"""
        if not amount:
            return None
        
        from_currency = from_currency.upper()
        
        if from_currency == 'AUD':
            return amount
        elif from_currency == 'USD':
            rate = self.get_usd_to_aud_rate()
            return amount * rate
        else:
            # For other currencies, you could add more conversion logic
            logging.warning(f"Unsupported currency: {from_currency}, treating as AUD")
            return amount
