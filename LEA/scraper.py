import json
import uuid
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import random
from urllib.parse import urljoin
import logging
import re

class LeaClothingScraper:
    def __init__(self, base_url: str = "https://www.leaclothingco.com"):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_page_content(self, url: str, max_retries: int = 3) -> BeautifulSoup:
        """Fetch and parse a webpage with retry logic and rate limiting"""
        for attempt in range(max_retries):
            try:
                # Add delay between requests (increasing with each retry)
                if attempt > 0:
                    delay = min(30, 5 * (2 ** attempt))  # Exponential backoff, max 30 seconds
                    self.logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Add a random delay between 3-7 seconds after successful requests
                time.sleep(random.uniform(3, 7))
                
                return BeautifulSoup(response.text, 'html.parser')
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    self.logger.warning(f"Rate limited on attempt {attempt + 1}/{max_retries}. URL: {url}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"Max retries reached for {url}")
                        return None
                else:
                    self.logger.error(f"HTTP error fetching {url}: {str(e)}")
                    return None
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {str(e)}")
                return None
        
        return None

    def extract_product_data(self, product_element) -> Dict[str, Any]:
        """Extract product data from a product element"""
        try:
            # Extract product name and URL
            name_element = product_element.select_one('.ProductItem__Title a')
            name = name_element.text.strip() if name_element else None
            product_url = urljoin(self.base_url, name_element['href']) if name_element else None
            VENDOR_ID = "7c9e130b-8920-4914-853e-64ee867bb3b4"


            # Visit the individual product page
            product_soup = self.get_page_content(product_url)
            if not product_soup:
                return None

            # Extract prices
            current_price = None
            original_price = None
            
            # Try multiple price selectors
            price_selectors = [
                '.ProductMeta__PriceList .ProductMeta__Price.Price--highlight',
                '.ProductMeta__PriceList .ProductMeta__Price',
                '.ProductMeta__Price',
                '.price',
                '[data-product-price]'
            ]
            
            for selector in price_selectors:
                price_element = product_soup.select_one(selector)
                if price_element:
                    try:
                        price_text = price_element.text.strip()
                        # Remove currency symbols and clean the price
                        price_text = price_text.replace('Rs.', '').replace('₹', '').replace(',', '').strip()
                        # Extract the first number found
                        price_match = re.search(r'\d+(?:\.\d+)?', price_text)
                        if price_match:
                            current_price = float(price_match.group())
                            break
                    except Exception as e:
                        self.logger.warning(f"Error parsing price from {selector}: {str(e)}")
            
            # Try to find original price if available
            original_price_selectors = [
                '.ProductMeta__PriceList .ProductMeta__Price.Price--compareAt',
                '.ProductMeta__Price.Price--compareAt',
                '.compare-at-price',
                '[data-compare-price]'
            ]
            
            for selector in original_price_selectors:
                original_price_element = product_soup.select_one(selector)
                if original_price_element:
                    try:
                        price_text = original_price_element.text.strip()
                        # Remove currency symbols and clean the price
                        price_text = price_text.replace('Rs.', '').replace('₹', '').replace(',', '').strip()
                        # Extract the first number found
                        price_match = re.search(r'\d+(?:\.\d+)?', price_text)
                        if price_match:
                            original_price = float(price_match.group())
                            break
                    except Exception as e:
                        self.logger.warning(f"Error parsing original price from {selector}: {str(e)}")
            
            # Log if prices couldn't be extracted
            if current_price is None:
                self.logger.warning(f"Could not extract current price for product: {product_url}")
            if original_price is None:
                self.logger.info(f"No original price found for product: {product_url}")

            # Extract image URLs from product page
            images = []
            # First try to get images from the product slides
            slide_elements = product_soup.select('.Product__SlideItem.Product__SlideItem--image')
            for slide in slide_elements:
                # Get image element
                img = slide.select_one('.Image--fadeIn.lazyautosizes.Image--lazyLoaded, .Image--lazyLoad.Image--fadeIn')
                if img:
                    # Get the original image URL
                    original_src = img.get('data-original-src')
                    if not original_src:
                        # Try to get from data-src
                        data_src = img.get('data-src')
                        if data_src:
                            # Replace {width} with max width
                            max_width = img.get('data-max-width', '800')
                            original_src = data_src.replace('{width}x', f'{max_width}x')
                    
                    if original_src:
                        # Convert relative URL to absolute
                        if original_src.startswith('//'):
                            original_src = 'https:' + original_src
                        elif original_src.startswith('/'):
                            original_src = 'https://www.leaclothingco.com' + original_src
                        images.append(original_src)
            
            # If no slides found, try to get images from the product listing
            if not images:
                product_item = product_soup.select_one('.ProductItem')
                if product_item:
                    # Get main and alternate images
                    image_wrapper = product_item.select_one('.ProductItem__ImageWrapper')
                    if image_wrapper:
                        # Get main image
                        main_image = image_wrapper.select_one('.ProductItem__Image:not(.ProductItem__Image--alternate)')
                        if main_image:
                            # Get all available sizes from srcset
                            srcset = main_image.get('data-srcset', '')
                            if srcset:
                                # Get the largest size
                                largest_size = None
                                largest_width = 0
                                for size_info in srcset.split(','):
                                    size_info = size_info.strip()
                                    if ' ' in size_info:
                                        url, size = size_info.rsplit(' ', 1)
                                        width = int(size.replace('w', ''))
                                        if width > largest_width:
                                            largest_width = width
                                            largest_size = url
                                
                                if largest_size:
                                    if largest_size.startswith('//'):
                                        largest_size = 'https:' + largest_size
                                    elif largest_size.startswith('/'):
                                        largest_size = 'https://www.leaclothingco.com' + largest_size
                                    images.append(largest_size)
                        
                        # Get alternate image
                        alt_image = image_wrapper.select_one('.ProductItem__Image--alternate')
                        if alt_image:
                            # Get all available sizes from srcset
                            srcset = alt_image.get('data-srcset', '')
                            if srcset:
                                # Get the largest size
                                largest_size = None
                                largest_width = 0
                                for size_info in srcset.split(','):
                                    size_info = size_info.strip()
                                    if ' ' in size_info:
                                        url, size = size_info.rsplit(' ', 1)
                                        width = int(size.replace('w', ''))
                                        if width > largest_width:
                                            largest_width = width
                                            largest_size = url
                                
                                if largest_size:
                                    if largest_size.startswith('//'):
                                        largest_size = 'https:' + largest_size
                                    elif largest_size.startswith('/'):
                                        largest_size = 'https://www.leaclothingco.com' + largest_size
                                    images.append(largest_size)
            
            # Extract rating and reviews from product page
            rating = None
            review_count = None
            rating_element = product_soup.select_one('.jdgm-prev-badge')
            if rating_element:
                rating = float(rating_element.get('data-average-rating'))
                review_count = int(rating_element.get('data-number-of-reviews'))
            
            # Extract category from URL
            category = None
            if product_url:
                category = product_url.split('/products/')[0].split('/')[-1] if '/products/' in product_url else None

            # Extract description from product page
            description = ""
            desc_section = product_soup.select_one('#description')
            if desc_section:
                # Extract main description
                main_desc = desc_section.select_one('p')
                if main_desc:
                    description += main_desc.get_text(strip=True) + "\n\n"
                
                # Extract features
                features = desc_section.select('ul li')
                if features:
                    description += "Features:\n"
                    for feature in features:
                        description += f"- {feature.get_text(strip=True)}\n"
                
                # Extract usage suggestions
                usage = desc_section.select('p:not(:first-child)')
                if usage:
                    description += "\nUsage Suggestions:\n"
                    for p in usage:
                        text = p.get_text(strip=True)
                        if text:
                            description += f"{text}\n"

            # Extract product details from product page
            product_details = {}
            details_section = product_soup.select_one('#pro-details')
            if details_section:
                details_items = details_section.select('li')
                for item in details_items:
                    text = item.text.strip()
                    if ':' in text:
                        key, value = text.split(':', 1)
                        product_details[key.strip()] = value.strip()
                    else:
                        product_details[text] = True

            # Extract vendor details from product page
            vendor_details = {}
            vendor_section = product_soup.select_one('#vendor-details')
            if vendor_section:
                vendor_items = vendor_section.select('li')
                for item in vendor_items:
                    text = item.text.strip()
                    if ':' in text:
                        key, value = text.split(':', 1)
                        vendor_details[key.strip()] = value.strip()
                    else:
                        vendor_details[text] = True

            # Extract available sizes from product page
            available_sizes = []
            size_elements = product_soup.select('.SizeSwatchList .SizeSwatch')
            for size in size_elements:
                available_sizes.append(size.text.strip())

            # Extract color options from product page
            colors = []
            color_elements = product_soup.select('.ColorSwatchList .ColorSwatch')
            for color in color_elements:
                color_text = color.text.strip()
                if color_text:
                    colors.append(color_text)
            
            # Extract size chart from product page
            size_chart = {
                "inches": {},
                "cm": {}
            }
            size_chart_element = product_soup.select_one('.ks-table-wrapper')
            if size_chart_element:
                # Extract headers
                headers = [th.text.strip() for th in size_chart_element.select('.ks-table-header-cell')]
                
                # Extract inches measurements
                inch_table = size_chart_element.select_one('.inch-table')
                if inch_table:
                    for row in inch_table.select('tr')[1:]:  # Skip header row
                        cells = row.select('td')
                        if cells:
                            size = cells[0].text.strip()
                            measurements = {}
                            for i in range(1, len(cells)):
                                measurements[headers[i]] = cells[i].text.strip()
                            size_chart["inches"][size] = measurements
                
                # Extract cm measurements
                cm_table = size_chart_element.select_one('.cm-table')
                if cm_table:
                    for row in cm_table.select('tr')[1:]:  # Skip header row
                        cells = row.select('td')
                        if cells:
                            size = cells[0].text.strip()
                            measurements = {}
                            for i in range(1, len(cells)):
                                measurements[headers[i]] = cells[i].text.strip()
                            size_chart["cm"][size] = measurements

            # Extract colors from product name and description
            colors = set()
            if name:
                # Look for color in product name
                color_keywords = ['Black', 'White', 'Red', 'Blue', 'Green', 'Yellow', 'Pink', 'Purple', 'Orange', 'Brown', 'Grey', 'Beige']
                for color in color_keywords:
                    if color.lower() in name.lower():
                        colors.add(color)
            
            # Extract from description
            desc_section = product_soup.select_one('#description')
            if desc_section:
                desc_text = desc_section.get_text()
                for color in color_keywords:
                    if color.lower() in desc_text.lower():
                        colors.add(color)

            # Create meta data
            meta = {
                "category": category,
                "rating": rating,
                "review_count": review_count,
                "available_sizes": list(size_chart["inches"].keys()),
                "colors": list(colors),
                "product_details": product_details,
                "vendor_details": vendor_details,
                "size_chart": size_chart,
                "tags": [category] if category else [],
                "productUrl": product_url,
            }

            # Create price object
            price = {
                "default": current_price,
                "original": original_price,
                "meta": {
                    "CURRENCY_CODE": "INR",
                    "CURRENCY_LOGO": "Rs."
                }
            }
            
            product = {
                "label": name,
                "description": description,
                "images": images,
                "price": price,
                "meta": meta,
                # "url": product_url,
                "vendor_id": VENDOR_ID
            }
            return product
        except Exception as e:
            print(f"Error extracting product data: {str(e)}")
            return None

    def scrape_products(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape products from multiple URLs"""
        all_products = []
        
        for url in urls:
            self.logger.info(f"Scraping {url}...")
            soup = self.get_page_content(url)
            
            if not soup:
                continue
                
            # Find all product elements
            product_elements = soup.select('.ProductItem')
            for element in product_elements:
                product_data = self.extract_product_data(element)
                if product_data:
                    all_products.append(product_data)
                    
            # Add longer delay between collection pages
            time.sleep(random.uniform(5, 10))
            
        return all_products

    def save_to_json(self, products: List[Dict[str, Any]], filename: str = "lea_products.json"):
        """Save scraped products to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved {len(products)} products to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {str(e)}")

def main():
    # Example usage
    urls = [
        "https://www.leaclothingco.com/collections/corsets",
        "https://www.leaclothingco.com/collections/dresses",
        "https://www.leaclothingco.com/collections/tops",
        "https://www.leaclothingco.com/collections/coord-sets",
        "https://www.leaclothingco.com/collections/lea-jumpsuits",
        "https://www.leaclothingco.com/collections/lange-by-lea",
        "https://www.leaclothingco.com/collections/gowns",
        "https://www.leaclothingco.com/collections/loungewear",
        "https://www.leaclothingco.com/collections/bottoms",
        "https://www.leaclothingco.com/collections/accessories",
        "https://www.leaclothingco.com/collections/blouses",
        "https://www.leaclothingco.com/collections/lehengas",
        "https://www.leaclothingco.com/collections/sarees",
        "https://www.leaclothingco.com/collections/kurta-sets",


    ]
    
    scraper = LeaClothingScraper()
    products = scraper.scrape_products(urls)
    scraper.save_to_json(products)

if __name__ == "__main__":
    main() 