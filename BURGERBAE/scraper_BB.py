import json
import uuid
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import random
from urllib.parse import urljoin

class BurgerBaeScraper:
    def __init__(self, base_url: str = "https://www.burgerbaeclothing.com"):
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

    def get_product_tags(self, name: str, description: str, category: str) -> List[str]:
        """Extract relevant tags from product details"""
        # Define available tags
        available_tags = [
            "Hoodie", "Co-ords", "T-Shirts", "Baby Tees", "Cute Tops", 
            "Tanks", "Tops", "Shades", "Bottoms", "Dresses", 
            "Accessories", "Sweatshirts", "Camisole", "Crop Tops", "dress", "Hat", "Skirt", "Sweater","Y2K top"
        ]
        
        # Convert to lowercase for case-insensitive matching
        name_lower = name.lower()
        desc_lower = description.lower() if description else ""
        category_lower = category.lower() if category else ""
        
        # Initialize tags list
        tags = []
        
        # Check for tags in name
        for tag in available_tags:
            if tag.lower() in name_lower:
                tags.append(tag)
        
        # Check for tags in description
        for tag in available_tags:
            if tag.lower() in desc_lower and tag not in tags:
                tags.append(tag)
        
        # Check for tags in category
        for tag in available_tags:
            if tag.lower() in category_lower and tag not in tags:
                tags.append(tag)
        
        # Add specific tag mappings
        tag_mappings = {
            "hoodie": "Hoodies",
            "hoody": "Hoodies",
            "co ord": "Co-ords",
            "co-ord": "Co-ords",
            "co ords": "Co-ords",
            "co-ords": "Co-ords",
            "tshirt": "T-Shirts",
            "t shirt": "T-Shirts",
            "t-shirts": "T-Shirts",
            "baby tee": "Baby Tees",
            "crop top": "Cute Tops",
            "cute top": "Cute Tops",
            "tank top": "Tanks",
            "tanktop": "Tanks",
            "top": "Tops",
            "sunglasses": "Shades",
            "shade": "Shades",
            "pant": "Bottoms",
            "pants": "Bottoms",
            "jeans": "Bottoms",
            "dress": "Dresses",
            "jewelry": "Accessories",
            "jewellery": "Accessories",
            "accessory": "Accessories",
            "sweatshirt": "Sweatshirts",
            "sweat shirt": "Sweatshirts"
        }
        
        # Check for mapped tags
        for key, tag in tag_mappings.items():
            if (key in name_lower or key in desc_lower or key in category_lower) and tag not in tags:
                tags.append(tag)
        
        # If no tags found, add category as tag
        if not tags and category:
            tags.append(category)
        
        return tags

    def extract_product_data(self, product_element) -> Dict[str, Any]:
        """Extract product data from a product element"""
        try:
            print("Starting product data extraction...")
            
            # Hardcoded vendor ID for BurgerBae
            VENDOR_ID = "b255da59-029c-4fe4-b502-015487736e87"
            
            # Extract product name and URL
            name_element = product_element.select_one('.product-card-title')
            if not name_element:
                print("No name element found")
                return None
                
            name = name_element.text.strip()
            product_url = urljoin(self.base_url, name_element.get('href', ''))
            print(f"Found product: {name} at {product_url}")
            
            # Visit the product page to get description and size chart
            product_soup = self.get_page_content(product_url)
            description = None
            size_chart = None
            if product_soup:
                # Get description
                description_element = product_soup.select_one('.collapsible__content.accordion__content.rte')
                if description_element:
                    description = description_element.get_text(strip=True)
                    print("Found product description")
                
                # Get size chart
                size_chart_element = product_soup.select_one('.product-popup-modal__content-info img')
                if size_chart_element:
                    size_chart = size_chart_element.get('src', '')
                    if size_chart.startswith('//'):
                        size_chart = 'https:' + size_chart
                    elif size_chart.startswith('/'):
                        size_chart = self.base_url + size_chart
                    print("Found size chart image")
            
            # Extract prices
            current_price = None
            original_price = None
            price_element = product_element.select_one('.price')
            if price_element:
                # Extract current price
                current_price_text = price_element.select_one('.amount.discounted')
                if current_price_text:
                    current_price = float(current_price_text.text.strip().replace('Rs.', '').replace(',', '').strip())
                    print(f"Current price: {current_price}")
                
                # Extract original price
                original_price_text = price_element.select_one('del .amount')
                if original_price_text:
                    original_price = float(original_price_text.text.strip().replace('Rs.', '').replace(',', '').strip())
                    print(f"Original price: {original_price}")
            
            # Extract image URLs
            images = []
            # Get primary image
            primary_img = product_element.select_one('.product-primary-image')
            if primary_img:
                srcset = primary_img.get('data-srcset', '')
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
                            largest_size = 'https://www.burgerbaeclothing.com' + largest_size
                        images.append(largest_size)
                        print(f"Added primary image: {largest_size}")

            # Get secondary images
            secondary_imgs = product_element.select('.product-secondary-image')
            for img in secondary_imgs:
                srcset = img.get('data-srcset', '')
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
                            largest_size = 'https://www.burgerbaeclothing.com' + largest_size
                        images.append(largest_size)
                        print(f"Added secondary image: {largest_size}")
            
            # Extract rating
            rating = None
            rating_element = product_element.select_one('.star-rating')
            if rating_element:
                rating = float(rating_element.get('style', '').split(':')[1].strip().replace(';', ''))
                print(f"Rating: {rating}")
            
            # Extract category from URL
            category = None
            if product_url:
                category = product_url.split('/products/')[0].split('/')[-1] if '/products/' in product_url else None
                print(f"Category: {category}")

            # Extract available colors
            colors = []
            color_elements = product_element.select('.product-card-swatch')
            for color in color_elements:
                color_name = color.select_one('.visually-hidden')
                if color_name:
                    colors.append(color_name.text.strip())
            print(f"Colors: {colors}")

            # Extract available sizes
            sizes = []
            size_elements = product_element.select('.product-card-sizes--size span')
            for size in size_elements:
                sizes.append(size.text.strip())
            print(f"Sizes: {sizes}")

            # Get tags based on product details
            tags = self.get_product_tags(name, description, category)
            print(f"Extracted tags: {tags}")

            # Create meta data
            meta = {
                "rating": rating,
                "available_sizes": sizes,
                "colors": colors,
                "tags": tags,
                "on_sale": bool(original_price and current_price and original_price > current_price),
                "size_chart": size_chart,
                "productUrl": product_url
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
                "vendor_id": VENDOR_ID
            }
            print("Successfully created product object")
            return product
        except Exception as e:
            print(f"Error extracting product data: {str(e)}")
            return None

    def scrape_products(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape products from multiple URLs with pagination support"""
        all_products = []
        total_products = 0
        total_pages = 32  # Total number of pages
        
        for url in urls:
            print(f"\nScraping {url}...")
            page = 1
            
            while page <= total_pages:
                # Add page parameter to URL
                page_url = f"{url}?page={page}"
                print(f"\nScraping page {page}/{total_pages}...")
                
                soup = self.get_page_content(page_url)
                if not soup:
                    print(f"Failed to get content from {page_url}")
                    break
                
                # Find all product elements
                product_elements = soup.select('.product-card')
                print(f"Found {len(product_elements)} product elements on page {page}")
                
                if not product_elements:
                    print("No products found. Trying alternative selectors...")
                    product_elements = soup.select('.product-item')
                    print(f"Found {len(product_elements)} products with alternative selector")
                
                if not product_elements:
                    print("No products found on this page. Stopping pagination.")
                    break
                
                page_products = []
                for element in product_elements:
                    product_data = self.extract_product_data(element)
                    if product_data:
                        page_products.append(product_data)
                        print(f"Successfully extracted product: {product_data.get('label')}")
                    else:
                        print("Failed to extract product data from element")
                
                all_products.extend(page_products)
                total_products += len(page_products)
                print(f"\nProgress: Page {page}/{total_pages} - Total products so far: {total_products}/512")
                
                # Save progress after each page
                self.save_to_json(all_products, "burgerbae_products.json")
                
                # Move to next page
                page += 1
                
                # Add delay between pages
                if page <= total_pages:
                    delay = random.uniform(2, 4)
                    print(f"Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
            
            # Add delay between different URLs
            if url != urls[-1]:  # Don't wait after the last URL
                delay = random.uniform(3, 5)
                print(f"\nWaiting {delay:.1f} seconds before next URL...")
                time.sleep(delay)
            
        print(f"\nScraping completed! Total products scraped: {total_products}/512")
        return all_products

    def save_to_json(self, products: List[Dict[str, Any]], filename: str = "burgerbae_products.json"):
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
        "https://www.burgerbaeclothing.com/collections/for-womens",
        # Add more collection URLs as needed
    ]
    
    scraper = BurgerBaeScraper()
    products = scraper.scrape_products(urls)
    scraper.save_to_json(products)

if __name__ == "__main__":
    main()
