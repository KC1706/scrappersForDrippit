import json
import csv
import os

def read_csv_labels(csv_file):
    """Read product labels from CSV file."""
    labels = {}  # Changed to dict to store ID and Label
    # Try different encodings
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Label' in row and 'ID' in row:
                        labels[row['Label']] = row['ID']
            print(f"Successfully read CSV with {encoding} encoding")
            return labels
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading CSV with {encoding} encoding: {str(e)}")
            continue
    
    raise Exception("Could not read CSV file with any of the attempted encodings")

def get_json_products(json_file):
    """Get all products from JSON file."""
    products = {}
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_products = json.load(f)
            for product in json_products:
                if 'label' in product:
                    products[product['label']] = product
        return products
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        raise

def main():
    try:
        # File paths
        csv_file = 'products_with_null_prices.csv'
        json_file = 'lea_products.json'
        output_file = 'filtered_products.json'
        
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct full paths
        csv_path = os.path.join(current_dir, csv_file)
        json_path = os.path.join(current_dir, json_file)
        output_path = os.path.join(current_dir, output_file)
        
        # Read labels from CSV
        print("\nReading labels from CSV...")
        csv_labels = read_csv_labels(csv_path)
        print(f"Found {len(csv_labels)} unique labels in CSV")
        
        # Get products from JSON
        print("\nReading products from JSON...")
        json_products = get_json_products(json_path)
        print(f"Found {len(json_products)} unique products in JSON")
        
        # Find matching products and print comparison
        print("\nMatching Products:")
        print("-" * 100)
        print(f"{'CSV Label':<50} | {'JSON Label':<50}")
        print("-" * 100)
        
        matched_products = []
        for csv_label, csv_id in csv_labels.items():
            if csv_label in json_products:
                json_product = json_products[csv_label]
                print(f"{csv_label:<50} | {json_product['label']:<50}")
                matched_products.append(json_product)
        
        print("-" * 100)
        print(f"\nFound {len(matched_products)} matching products")
        
        # Save matched products
        print("\nSaving matched products...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(matched_products, f, indent=2)
        
        print(f"\nDone! Matched products saved to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()