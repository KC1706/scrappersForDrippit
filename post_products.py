import json
import requests
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_products(file_path: str) -> list:
    """
    Load products from JSON file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            products = json.load(file)
        logger.info(f"Successfully loaded {len(products)} products from {file_path}")
        return products
    except Exception as e:
        logger.error(f"Error loading products from {file_path}: {str(e)}")
        raise

def post_product(product: Dict[str, Any], api_url: str) -> bool:
    """
    Post a single product to the API
    """
    try:
        logger.info(f"Posting product: {product['label']}")
        response = requests.post(api_url, json=product)
        
        if response.status_code == 200:
            logger.info(f"Successfully posted product: {product['label']}")
            return True
        else:
            logger.error(f"Failed to post product {product['label']}. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error posting product {product['label']}: {str(e)}")
        return False

def main():
    # Configuration
    JSON_FILE_PATH = "./LEA/lea_products.json"
    API_URL = "http://127.0.0.1:5000/products"
    
    try:
        # Load products
        products = load_products(JSON_FILE_PATH)
        
        # Track success/failure
        total_products = len(products)
        successful_posts = 0
        failed_posts = 0
        
        # Post each product
        for index, product in enumerate(products, 1):
            logger.info(f"Processing product {index}/{total_products}")
            
            if post_product(product, API_URL):
                successful_posts += 1
            else:
                failed_posts += 1
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        # Print summary
        logger.info("\nPosting Summary:")
        logger.info(f"Total products processed: {total_products}")
        logger.info(f"Successful posts: {successful_posts}")
        logger.info(f"Failed posts: {failed_posts}")
        
    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}")

if __name__ == "__main__":
    main()
