import os

# GitHub Actions environment detection
IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'

# Scraping settings
CRAWL_DELAY_MIN = 2 if IS_GITHUB_ACTIONS else 1
CRAWL_DELAY_MAX = 5 if IS_GITHUB_ACTIONS else 3
MAX_RETRIES = 2 if IS_GITHUB_ACTIONS else 3
REQUEST_TIMEOUT = 15

# Default printer models to search for
DEFAULT_PRINTERS = [
    "Fargo DTC1250e",
    "Evolis Primacy 2", 
    "Zebra ZC300",
    "Magicard 600",
    "Entrust Sigma DS2",
    "Zebra ZC100",
    "Evolis Badgy200",
    "Magicard Pronto 100"
]

# Output settings
SAVE_HISTORICAL = True
SAVE_JSON = True
SAVE_CSV = True
GENERATE_SUMMARY = True

# Currency settings
DEFAULT_CURRENCY = 'AUD'
SUPPORTED_CURRENCIES = ['USD', 'AUD', 'EUR', 'GBP']

# Notification settings
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')
EMAIL_NOTIFICATIONS = os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'

# Debug settings
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
VERBOSE_LOGGING = IS_GITHUB_ACTIONS or DEBUG_MODE
