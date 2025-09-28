# Test Equipment Multi-Site Scraper

A comprehensive Python web scraping + Streamlit application that searches multiple test equipment websites and Google for product data.

## Features

### 🔍 Multi-Site Scraping
- **eBay**: Search with price filtering (> $1000)
- **Valuetronics.com**: Test equipment marketplace
- **TestEquipment.center**: Equipment sales and rentals  
- **TestWorld.com**: Used test equipment
- **Google Search**: Top 5 non-ad results

### 📊 Data Analysis
- Excel file analysis for sample brand/model patterns
- Interactive Streamlit interface
- JSON and CSV output formats
- Real-time progress tracking

### 🎯 Target Data Fields
For each product found, the system extracts:
- `brand` (equipment brand)
- `model` (model number)
- `price` (product price)
- `vendor` (site/vendor name)
- `web_url` (exact product page URL)
- `qty_available` (quantity if available)
- `source` (e.g., "ebay", "valuetronics", etc.)

## Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Usage

### Basic Search
1. Enter the equipment **brand** (e.g., Agilent, Keysight, Tektronix)
2. Enter the **model** number (e.g., 8116A, 34401A, MSO64)
3. Click **Search All Sites**

### Excel Analysis
- Place your Excel file named `quote-equipment.xlsx` in the project directory
- The app will automatically analyze it for brand/model patterns
- Expects columns: `eqbrand` (first word = brand) and `model`

### Configuration Options
- **Site Selection**: Choose which websites to search
- **Results Limit**: Set maximum results per site (1-20)
- **Excel Analysis**: Toggle sample data analysis

## Output Format

Results are returned in structured JSON format:

```json
{
  "web_scraping_results": [
    {
      "brand": "Agilent",
      "model": "8116A", 
      "price": "$1,850.00",
      "vendor": "Valuetronics",
      "web_url": "https://valuetronics.com/product/Agilent-8116A",
      "qty_available": "In Stock",
      "source": "valuetronics"
    }
  ]
}
```

## Project Structure

```
├── app.py                    # Main Streamlit application
├── multi_site_scraper.py     # Core scraping functionality
├── excel_reader.py           # Excel file analysis
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── quote-equipment.xlsx      # Sample Excel data (optional)
```

## Core Components

### MultiSiteScraper Class
- Handles scraping across all target websites
- Implements rate limiting and error handling
- Provides fallback sample data for demonstration

### Key Features
- **Rate Limiting**: Random delays between requests
- **Error Handling**: Graceful failure with informative messages
- **URL Validation**: Ensures proper link formatting
- **Price Filtering**: eBay results filtered for > $1000
- **Fallback Data**: Sample results when sites block scraping

## Dependencies

- `streamlit` - Web interface
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `openpyxl` - Excel file reading
- `googlesearch-python` - Google search functionality

## Technical Notes

### Scraping Challenges
- Many sites have anti-bot protection
- Rate limiting required to avoid detection
- CSS selectors may change over time
- Some sites may return 403/503 errors

### Demonstration Mode
When live scraping fails, the system provides realistic sample data to demonstrate the expected output format and functionality.

### eBay Specific
- Only returns products with price > $1000
- Filters out sponsored/promoted listings
- Extracts seller information when available

## Example Search Terms

**Popular Test Equipment Brands:**
- Agilent (8116A, 34401A, E5071C)
- Keysight (N9000A, E4980A, M9804A)
- Tektronix (MSO64, AWG70001A, DPO7254C)
- Rohde & Schwarz (FSW, ZNB, RTB2004)
- Anritsu (MS2760A, MT8870A, MU100020A)

## Troubleshooting

### Common Issues
1. **No Results Found**: Try different brand/model combinations
2. **Connection Errors**: Check internet connectivity
3. **403/503 Errors**: Websites may be blocking requests (fallback data will be used)
4. **Excel Analysis Fails**: Ensure Excel file has `eqbrand` and `model` columns

### Development Notes
- The scraper includes extensive error handling
- Debug output is printed to console
- Sample data ensures consistent demonstration of functionality
- Rate limiting prevents overwhelming target websites

## License

This project is for educational and demonstration purposes. Always respect website terms of service and implement appropriate rate limiting when scraping.
