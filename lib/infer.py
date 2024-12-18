# infer the name and thumbnail image from uri

from bs4 import BeautifulSoup
from io import BytesIO
import re
from PIL import Image
import boto3
from .config import S3_BUCKET
import requests
from selenium import webdriver
from pyvirtualdisplay import Display

def open_display():
    # Set up a virtual display using Xvfb
    display = Display(visible=0, size=(800, 600))
    display.start()

    # Set up the Selenium web driver with headless options
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return (display, driver)

def close_display(display, driver):
    # Terminate the Xvfb instance
    display.stop()

    # Quit the Selenium driver
    driver.quit()

def infer_details(uri, save_thumbnail=False):

    # Get the webpage content
    try:
        response = requests.get(uri)
    except:
        print("Cannot retrieve url: " + uri)
        return(uri, None)

    try:
      jc = response.json()
      if jc:
         return (jc.get('name'), jc.get('image'))
    except Exception as e:
      print("Its not json")

    content = response.content

    # Parse the webpage content using Beautiful Soup
    soup = BeautifulSoup(content, 'html.parser')

    # Get the title tag from the HTML
    title_tag = soup.title
    name = None
    if re.search('forbidden', title_tag.text, re.IGNORECASE):
       print("Forbidden response from uri: " + uri)
       return(uri, None)

    # Try to get the text content of the title tag
    if title_tag is not None and title_tag.string:
        name = title_tag.string.strip()

    # If the title tag is not found or has no text content, try the first h1 tag
    if not name:
        h1_tag = soup.find('h1')
        if h1_tag is not None:
            name = h1_tag.string.strip()

    # If the h1 tag is not found or has no text content, try the meta title tag
    if not name:
        meta_title_tag = soup.find('meta', attrs={'name': 'title'})
        if meta_title_tag is not None:
            name = meta_title_tag['content'].strip()
        # Get the text content of the title tag
        if title_tag is not None:
            name = title_tag.string

    if not name:
        name = uri

    if not save_thumbnail:
        return (name, None)

    try:
        (display, driver) = open_display()
    except Exception as e:
        print("Exception trying to open display: " + str(e) + " skipping")
        return(name, None)

    # Set the desired thumbnail size
    thumbnail_size = (200, 200)

    # Create a thumbnail of the webpage
    driver.get(uri)
    screenshot = driver.get_screenshot_as_png()
    if screenshot is not None:
        # Open the image using PIL
        img = Image.open(BytesIO(screenshot))

        # Create the thumbnail
        img.thumbnail(thumbnail_size)

        # Save the thumbnail to a BytesIO object
        thumbnail_io = BytesIO()
        img.save(thumbnail_io, format='PNG')

        # Store the thumbnail to S3
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(S3_BUCKET)
        object_key = 'thumbnails/' + uri.replace('/', '_') + '.png'
        bucket.put_object(Key=object_key, Body=thumbnail_io.getvalue())

        # Get the URL to the stored thumbnail
        thumbnail_url = s3.meta.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': object_key,
            }
        )
        print("Saved image to : " + thumbnail_url)
        close_display(display, driver)
        return(name, thumbnail_url)
