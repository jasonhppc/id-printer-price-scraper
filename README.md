# ID Printer Price Scraper

Automated price monitoring for plastic ID card printers in Australia with USD to AUD conversion.

## Features

- 🤖 **Automated Daily Scraping** via GitHub Actions
- 💱 **Currency Conversion** (USD → AUD with live exchange rates)
- 🏪 **Multi-Store Support** (Australian and US suppliers)
- 📊 **Price History Tracking** 
- ⚙️ **Configurable Websites** via JSON
- 📈 **Summary Statistics** and best deal detection

## Monitored Printers

- Fargo DTC1250e
- Evolis Primacy 2
- Zebra ZC300
- Magicard 600
- Entrust Sigma DS2
- And more...

## Supported Stores

### Australian Suppliers (AUD)
- Officeworks
- JB Hi-Fi
- Harvey Norman

### US Suppliers (USD → AUD)
- Bodno
- ID Card Group  
- Easy Badges

## Configuration

Edit `src/website_configs.json` to:
- Add/remove websites
- Enable/disable specific stores
- Add new printer models
- Customize CSS selectors

## Manual Run

```bash
cd src
python scraper.py
