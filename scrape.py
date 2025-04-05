import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


def scrape_hyperlinks(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Failed to retrieve content: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    text_content = " ".join([p.text for p in soup.find_all("p")])

    return {"content": text_content}

# Function to fetch product data from JSON-LD
def fetch_product_data_from_jsonld(soup):
    jsonld_script = soup.find('script', type='application/ld+json')
    if not jsonld_script:
        return None

    try:
        jsonld_data = json.loads(jsonld_script.string)
    except json.JSONDecodeError:
        return None

    if isinstance(jsonld_data, list):
        product_data = next((item for item in jsonld_data if item.get('@type') == 'Product'), None)
        if not product_data:
            return None
    elif isinstance(jsonld_data, dict) and jsonld_data.get('@type') == 'Product':
        product_data = jsonld_data
    else:
        return None

    # Handling offers which could be a list or a dictionary
    offers = product_data.get('offers')
    if isinstance(offers, list):
        product_price = next((offer.get('price') for offer in offers if offer.get('price')), '')
    elif isinstance(offers, dict):
        product_price = offers.get('price', '')
    else:
        product_price = ''

    extracted_data = {
        "product_name": product_data.get('name', ''),
        "product_price": product_price,
        "product_url": product_data.get('url', ''),
        "product_image_url": product_data.get('image', ''),
        "product_description": product_data.get('description', '')
    }

    return extracted_data

# Function to fetch product data from meta tags
def fetch_product_data_from_meta(soup, base_url):
    product_name = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'twitter:title'})
    product_price = soup.find('meta', attrs={'property': 'product:price:amount'}) or soup.find('meta', attrs={'name': 'price'})
    product_url = soup.find('meta', attrs={'property': 'og:url'}) or soup.find('meta', attrs={'name': 'twitter:url'})
    product_image_url = soup.find('meta', attrs={'property': 'og:image'}) or soup.find('meta', attrs={'name': 'twitter:image'})
    product_description = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'twitter:description'})

    extracted_data = {
        "product_name": product_name['content'] if product_name else '',
        "product_price": product_price['content'] if product_price else '',
        "product_url": product_url['content'] if product_url else '',
        "product_image_url": urljoin(base_url, product_image_url['content']) if product_image_url else '',
        "product_description": product_description['content'] if product_description else ''
    }

    return extracted_data

# Function to fetch product data from a webpage
def fetch_product_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to fetch product data from JSON-LD
    product_data = fetch_product_data_from_jsonld(soup)
    if product_data:
        return product_data

    # If JSON-LD is not available, fetch product data from meta tags
    return fetch_product_data_from_meta(soup, url)

# Main function to get the product data from a URL
def main():
    url = input("Enter the product URL: ").strip()
    product_data = fetch_product_data(url)

    if product_data:
        print("\nProduct Data Retrieved:")
        print(f"Product Name: {product_data['product_name']}")
        print(f"Product Price: {product_data['product_price']}")
        print(f"Product URL: {product_data['product_url']}")
        print(f"Product Image URL: {product_data['product_image_url']}")
        print(f"Product Description: {product_data['product_description']}")
    else:
        print("No product data found.")

if __name__ == '__main__':
    main()
