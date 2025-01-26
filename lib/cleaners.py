import re
from urllib.parse import urlparse, urlunparse

import requests


# if its just a word or string construct a uri for it
def construct_uri(word, issuer_id="anon"):
    return "https://linkedtrust.us/issuer/{}/labels/{}".format(issuer_id, word)


# if its a valid uri or has a valid http or https return that
def normalize_uri(uri, issuer_id=None):
    # Parse the URL and lowercase the domain name
    parsed_url = urlparse(uri)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path

    # if domain is empty, try to detect domain pattern
    if not domain:
        domain_pattern = r"^([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/.*)?$"
        if re.match(domain_pattern, uri):
            # Split at first slash to separate domain from path
            parts = uri.split("/", 1)
            domain = parts[0].lower()
            path = "/" + parts[1] if len(parts) > 1 else ""

    print(f"Domain: {domain}  Path:{path}")

    # Add the http or https prefix if necessary
    if parsed_url.scheme:
        scheme = parsed_url.scheme
    elif domain:
        # Check if the URL is valid and add the https prefix if it is
        response = requests.get(f"https://{domain}{path}")
        if response.ok:
            scheme = "https"
        elif requests.get(f"http://{domain}{path}").ok:
            scheme = "http"
        else:
            return construct_uri(uri)
    else:
        return uri

    # Construct the normalized URL and return it
    normalized_url = urlunparse((scheme, domain, path, "", "", ""))
    return normalized_url


def make_subject_uri(raw_claim):
    """Even tho we are interested in using claim address in future, for now we stick to
    the same method used by the app for consistency"""
    return "https://live.linkedtrust.us/claims/{}".format(raw_claim["id"])
