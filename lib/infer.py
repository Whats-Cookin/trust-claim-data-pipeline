# infer the name and thumbnail image from uri

import json
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


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


def extract_image_from_html(soup, base_uri):
    """
    Extract the best available image URL from HTML.
    Checks meta tags, schema.org JSON-LD, and common image patterns.
    Returns absolute URL or None.
    """
    image_url = None

    # Strategy 1: Open Graph image (most widely used)
    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image and og_image.get("content"):
        image_url = og_image.get("content").strip()

    # Strategy 2: Twitter/X card image
    if not image_url:
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            image_url = twitter_image.get("content").strip()

    # Strategy 3: Schema.org JSON-LD
    if not image_url:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                # Handle both single object and array of objects
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        img = item.get("image")
                        if img:
                            # image can be string or object with url property
                            if isinstance(img, str):
                                image_url = img
                            elif isinstance(img, dict):
                                image_url = img.get("url")
                            elif isinstance(img, list) and img:
                                first = img[0]
                                image_url = first if isinstance(first, str) else first.get("url")
                            if image_url:
                                break
                if image_url:
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    # Strategy 4: Apple touch icon (usually high quality site logo)
    if not image_url:
        apple_icon = soup.find("link", rel="apple-touch-icon")
        if apple_icon and apple_icon.get("href"):
            image_url = apple_icon.get("href").strip()

    # Strategy 5: Favicon as last resort
    if not image_url:
        favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if favicon and favicon.get("href"):
            image_url = favicon.get("href").strip()

    # Make URL absolute if relative
    if image_url and not image_url.startswith(('http://', 'https://', '//')):
        image_url = urljoin(base_uri, image_url)
    elif image_url and image_url.startswith('//'):
        image_url = 'https:' + image_url

    return image_url


def infer_details(uri, save_thumbnail=False):
    """
    Function to infer details from a URI including name and thumbnail.
    Extracts name from title/meta tags and image from og:image, schema.org, etc.

    Args:
        uri: The URI to fetch and parse
        save_thumbnail: If True, attempt to extract an image URL (no longer uses Selenium)

    Returns:
        Tuple of (name, image_url) where either can be None
    """
    print(f"Inferring details for: {uri}")
    name = None
    image_url = None

    # Default fallback name
    fallback_name = extract_fallback_name(uri)

    # Skip non-http URIs
    if not uri or not uri.startswith(('http://', 'https://')):
        print(f"Skipping non-http URI: {uri}")
        return (fallback_name, None)

    # Get the webpage content with timeout
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(uri, headers=headers, timeout=10)

        # Handle redirect
        if response.history:
            print(f"Redirected from {uri} to {response.url}")
            uri = response.url

        # Try to parse JSON if content type indicates JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                json_data = response.json()
                if json_data:
                    name = json_data.get('name') or json_data.get('title')
                    image_url = json_data.get('image') or json_data.get('thumbnail')
                    if name:
                        return (name, image_url)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from {uri}")

        # Parse as HTML
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract name - try multiple strategies
            # Strategy 1: Title tag
            title_tag = soup.title
            if title_tag and title_tag.string:
                name = title_tag.string.strip()

            # Strategy 2: H1 tag
            if not name:
                h1_tag = soup.find("h1")
                if h1_tag:
                    name = h1_tag.get_text().strip()

            # Strategy 3: Meta tags for title
            if not name:
                for meta in [
                    soup.find("meta", attrs={"property": "og:title"}),
                    soup.find("meta", attrs={"name": "title"}),
                    soup.find("meta", attrs={"name": "twitter:title"}),
                ]:
                    if meta and meta.get('content'):
                        name = meta.get('content').strip()
                        if name:
                            break

            # Extract image if requested
            if save_thumbnail:
                image_url = extract_image_from_html(soup, uri)

    except requests.RequestException as e:
        print(f"Request error for {uri}: {e}")
    except Exception as e:
        print(f"Error processing {uri}: {e}")

    # Use fallback name if nothing found
    if not name:
        name = fallback_name
        print(f"Using fallback name: {name}")

    return (name, image_url)


# Keep for backwards compatibility but just delegates to infer_details
def generate_thumbnail(uri):
    """
    Legacy function - now just extracts og:image etc. instead of taking screenshots.
    Returns image URL or None.
    """
    _, image_url = infer_details(uri, save_thumbnail=True)
    return image_url
