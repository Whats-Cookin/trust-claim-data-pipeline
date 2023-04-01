import requests
from urllib.parse import urlparse, urlunparse


# if its just a word or string construct a uri for it
def construct_uri(word, issuer_id='anon'):
    return 'https://linkedtrust.us/issuer/{}/labels/{}'.format(issuer_id, word)


# if its a valid uri or has a valid http or https return that
def normalize_uri(uri, issuer_id=None):
    # Parse the URL and lowercase the domain name
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path

    # Add the http or https prefix if necessary
    if not parsed_url.scheme:
        # Check if the URL is valid and add the https prefix if it is
        response = requests.get(f"https://{domain}{path}")
        if response.ok:
            scheme = "https"
        elsif (requests.get(f"http://{domain}{path}").ok):
            scheme = "http"
        else:
            return(construct_uri(uri))
    else:
        scheme = parsed_url.scheme

    # Construct the normalized URL and return it
    normalized_url = urlunparse((scheme, domain, path, "", "", ""))
    return normalized_url
