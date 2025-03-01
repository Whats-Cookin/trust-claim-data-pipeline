# infer the name and thumbnail image from uri

import re
from io import BytesIO
from pprint import pprint
from urllib.parse import urlparse

import boto3
import requests
from bs4 import BeautifulSoup
from PIL import Image
from pyvirtualdisplay import Display
from selenium import webdriver

from .config import S3_BUCKET


def open_display():
    # Set up a virtual display using Xvfb
    display = Display(visible=0, size=(800, 600))
    display.start()

    # Set up the Selenium web driver with headless options
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return (display, driver)


def close_display(display, driver):
    # Terminate the Xvfb instance
    display.stop()

    # Quit the Selenium driver
    driver.quit()

def normalize_uri(uri, issuer_id=None):
    """
    Normalize a URI to ensure consistency
    """
    # Trim whitespace
    uri = uri.strip()
    
    # Handle relative URLs if issuer_id is provided
    if uri.startswith('/') and issuer_id:
        try:
            parsed_issuer = urlparse(issuer_id)
            uri = f"{parsed_issuer.scheme}://{parsed_issuer.netloc}{uri}"
        except Exception as e:
            print(f"Error normalizing URI with issuer: {e}")
    
    # Ensure proper protocol
    if not uri.startswith('http://') and not uri.startswith('https://'):
        uri = f"https://{uri}"
        
    return uri

def extract_fallback_name(uri):
    """
    Extract a readable name from the URI as fallback
    """
    try:
        parsed_url = urlparse(uri)
        
        # Try to use path if available
        if parsed_url.path and parsed_url.path != '/':
            path_segments = [segment for segment in parsed_url.path.split('/') if segment]
            if path_segments:
                # Format the last segment
                name = path_segments[-1]
                # Replace hyphens and underscores with spaces
                name = name.replace('-', ' ').replace('_', ' ')
                # Capitalize words
                name = ' '.join(word.capitalize() for word in name.split())
                return name
                
        # Fallback to hostname
        hostname = parsed_url.netloc
        # Remove www. if present
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        return hostname
    except Exception as e:
        print(f"Error extracting fallback name: {e}")
        return uri

def infer_details(uri, save_thumbnail=False):
    """
    Function to infer details from a URI including name and thumbnail
    with error handling and fallback mechanisms
    """
    print(f"Inferring details for: {uri}")
    name = None
    thumbnail_url = None
    
    # Default fallback name
    fallback_name = extract_fallback_name(uri)
    
    # Get the webpage content with timeout and retry
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Make request with timeout
        response = requests.get(uri, headers=headers, timeout=10)
        
        # Handle redirect if needed
        if response.history:
            print(f"Request was redirected from {uri} to {response.url}")
            uri = response.url
        
        # Try to parse JSON if content type is application/json
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                json_data = response.json()
                if json_data:
                    # Extract name and image from JSON
                    if 'name' in json_data:
                        name = json_data.get('name')
                    elif 'title' in json_data:
                        name = json_data.get('title')
                        
                    # Extract thumbnail
                    if 'image' in json_data:
                        thumbnail_url = json_data.get('image')
                    elif 'thumbnail' in json_data:
                        thumbnail_url = json_data.get('thumbnail')
                        
                    if name:
                        return (name, thumbnail_url)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from {uri}")
        
        # If not JSON or no name from JSON, parse as HTML
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Strategy 1: Title tag
            title_tag = soup.title
            if title_tag is not None and title_tag.string:
                name = title_tag.string.strip()
                
            # Strategy 2: H1 tag
            if not name or not name.strip():
                h1_tag = soup.find("h1")
                if h1_tag is not None:
                    name = h1_tag.get_text().strip()
                    
            # Strategy 3: Meta tags
            if not name or not name.strip():
                # Try various meta tags
                meta_tags = [
                    soup.find("meta", attrs={"name": "title"}),
                    soup.find("meta", attrs={"property": "og:title"}),
                    soup.find("meta", attrs={"name": "twitter:title"})
                ]
                
                for meta_tag in meta_tags:
                    if meta_tag is not None and meta_tag.get('content'):
                        name = meta_tag.get('content').strip()
                        if name:
                            break
                            
            # Strategy 4: Look for prominent headings
            if not name or not name.strip():
                for heading in soup.select('header h1, header h2, main h1, main h2, .header h1, .header h2'):
                    name = heading.get_text().strip()
                    if name:
                        break
    
    except requests.RequestException as e:
        print(f"Request error for {uri}: {e}")
    except Exception as e:
        print(f"Error processing {uri}: {e}")
    
    # Use fallback name if no name found
    if not name or not name.strip():
        name = fallback_name
        print(f"Using fallback name: {name}")
    
    # Generate thumbnail if requested
    if save_thumbnail:
        try:
            thumbnail_url = generate_thumbnail(uri)
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
    
    return (name, thumbnail_url)


# separate function for thumbnail generation
def generate_thumbnail(uri):
    """
    Generate a thumbnail for a URI with better error handling
    """
    display = None
    driver = None
    
    try:
        # Open virtual display and browser
        display, driver = open_display()
        
        # Set the desired thumbnail size
        thumbnail_size = (200, 200)
    
        # Navigate to the URI with timeout
        driver.set_page_load_timeout(20)
        driver.get(uri)
        
        # Wait for page to load
        time.sleep(3)
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        if screenshot is None:
            print(f"Failed to capture screenshot for {uri}")
            return None
            
        # Open the image using PIL
        img = Image.open(BytesIO(screenshot))
    
        # Create the thumbnail
        img.thumbnail(thumbnail_size)
    
        # Save the thumbnail to a BytesIO object
        thumbnail_io = BytesIO()
        img.save(thumbnail_io, format="PNG")
    
        # Store the thumbnail to S3
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(S3_BUCKET)
        
        # Use safe key by replacing invalid chars
        safe_uri = re.sub(r'[^\w\-\.]', '_', uri)
        object_key = f"thumbnails/{safe_uri}.png"
        
        bucket.put_object(
            Key=object_key, 
            Body=thumbnail_io.getvalue(),
            ContentType='image/png'
        )
    
        # Get the URL to the stored thumbnail
        thumbnail_url = s3.meta.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=604800  # URL valid for 1 week
        )
        
        print(f"Saved image to: {thumbnail_url}")
        return thumbnail_url
        
    except Exception as e:
        print(f"Error generating thumbnail for {uri}: {e}")
        return None
        
    finally:
        # Always clean up resources
        if display and driver:
            try:
                close_display(display, driver)
            except Exception as e:
                print(f"Error closing display: {e}")
