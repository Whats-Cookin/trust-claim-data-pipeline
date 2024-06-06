import requests
from urllib.parse import urlparse, urlunparse


# if its just a word or string construct a uri for it
def construct_uri(word, issuer_id='anon'):
    return 'https://linkedtrust.us/issuer/{}/labels/{}'.format(issuer_id, word)


# if its a valid uri or has a valid http or https return that
def normalize_uri(uri, issuer_id=None):
    # Parse the URL and lowercase the domain name
    parsed_url = urlparse(uri)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path

    # Add the http or https prefix if necessary
    if parsed_url.scheme:
        scheme = parsed_url.scheme
    elif domain:
        # Check if the URL is valid and add the https prefix if it is
        response = requests.get(f"https://{domain}{path}")
        if response.ok:
            scheme = "https"
        elif (requests.get(f"http://{domain}{path}").ok):
            scheme = "http"
        else:
            return(construct_uri(uri))
    else:
        return uri

    # Construct the normalized URL and return it
    normalized_url = urlunparse((scheme, domain, path, "", "", ""))
    return normalized_url

def make_subject_uri(raw_claim):
    """ if the claim has a claim address return that else construct a uri for it """
    return raw_claim['claimAddress'] or 'https://live.linkedtrust.us/claims/${}'.format(raw_claim['id'])
