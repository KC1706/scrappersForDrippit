import json
import re
import csv
import pandas as pd

def load_products(filename: str) -> list[dict]:
    """Load products from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return []

def save_products(products: list[dict], filename: str):
    """Save products to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(products)} products to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")

def is_men_only_product(product: dict) -> bool:
    """Check if a product is men-only"""
    # Keywords that indicate men-only products
    men_only_keywords = [
        r'\bmen\b',
        r'\bman\b',
        r'\bgentleman\b',
        r'\bgents\b',
        r'\bboys\b',
        r'\bguys\b',
        r'\bmale\b'
    ]
    
    # Keywords that indicate unisex or women's products
    unisex_keywords = [
        r'\bunisex\b',
        r'\bwomen\b',
        r'\bwoman\b',
        r'\bgirls\b',
        r'\bfemale\b',
        r'\bfor men and women\b',
        r'\bfor women and men\b'
    ]
    
    # Check product label and description
    text = f"{product.get('label', '').lower()} {product.get('description', '').lower()}"
    
    # If any unisex keywords are found, it's not men-only
    for keyword in unisex_keywords:
        if re.search(keyword, text):
            return False
    
    # If any men-only keywords are found, it's men-only
    for keyword in men_only_keywords:
        if re.search(keyword, text):
            return True
    
    return False

def filter_products(products: list[dict]) -> list[dict]:
    """Filter out men-only products"""
    filtered_products = []
    men_only_count = 0
    
    for product in products:
        if is_men_only_product(product):
            men_only_count += 1
            print(f"Removing men-only product: {product.get('label')}")
        else:
            filtered_products.append(product)
    
    print(f"\nRemoved {men_only_count} men-only products")
    print(f"Kept {len(filtered_products)} products")
    return filtered_products

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv_file(file_path):
    return pd.read_csv(file_path)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    # Load the files
    products = load_json_file('lea_products.json')
    null_prices_df = load_csv_file('products_with_null_prices.csv')
    
    # Get list of labels from null_prices_df
    null_price_labels = set(null_prices_df['Label'].str.strip())
    
    # Filter products that match the labels
    matched_products = []
    for product in products:
        if product['label'] in null_price_labels:
            matched_products.append(product)
    
    # Save matched products to a new JSON file
    save_json_file(matched_products, 'matched_products.json')
    
    print(f"Found {len(matched_products)} matching products out of {len(products)} total products")
    print(f"Looking for {len(null_price_labels)} products with null prices")

if __name__ == "__main__":
    main() 