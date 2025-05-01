import json
import uuid
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import random
from urllib.parse import urljoin

class LeaClothingScraper:
    def __init__(self, base_url: str = "https://www.leaclothingco.com"):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_page_content(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def extract_product_data(self, product_element) -> Dict[str, Any]:
        """Extract product data from a product element"""
        try:
            # Extract product name and URL
            name_element = product_element.select_one('.ProductItem__Title a')
            name = name_element.text.strip() if name_element else None
            product_url = urljoin(self.base_url, name_element['href']) if name_element else None
            VENDOR_ID = "3c4f5d92-7a3e-49a2-a4b6-8ef9a6d9c1e3"


            # Visit the individual product page
            product_soup = self.get_page_content(product_url)
            if not product_soup:
                return None

            # Extract prices
            current_price = None
            original_price = None
            price_list = product_soup.select_one('.ProductMeta__PriceList')
            if price_list:
                # Extract current price
                current_price_element = price_list.select_one('.ProductMeta__Price.Price--highlight')
                if current_price_element:
                    current_price = float(current_price_element.text.strip().replace('Rs.', '').replace(',', '').strip())
                
                # Extract original price
                original_price_element = price_list.select_one('.ProductMeta__Price.Price--compareAt')
                if original_price_element:
                    original_price = float(original_price_element.text.strip().replace('Rs.', '').replace(',', '').strip())
            
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
                "CATEGORY": category,
                "RATING": rating,
                "REVIEW_COUNT": review_count,
                "AVAILABLE_SIZES": list(size_chart["inches"].keys()),
                "COLORS": list(colors),
                "PRODUCT_DETAILS": product_details,
                "VENDOR_DETAILS": vendor_details,
                "SIZE_CHART": size_chart,
                "ORIGINAL_PRICE": original_price,
                "TAGS": [category] if category else []
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
                "id": str(uuid.uuid4()),
                "label": name,
                "description": description,
                "images": images,
                "price": price,
                "meta": meta,
                "url": product_url,
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
            print(f"Scraping {url}...")
            soup = self.get_page_content(url)
            
            if not soup:
                continue
                
            # Find all product elements
            product_elements = soup.select('.ProductItem')
            for element in product_elements:
                product_data = self.extract_product_data(element)
                if product_data:
                    all_products.append(product_data)
                    
            # Add delay to be respectful to the website
            time.sleep(random.uniform(1, 3))
            
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