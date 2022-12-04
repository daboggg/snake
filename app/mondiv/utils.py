import os

from polygon import RESTClient

client = RESTClient(os.environ.get("POLYGON_API_KEY"))

def get_upl_and_apiKey(url):
    return url+'?apiKey='+os.environ.get('POLYGON_API_KEY')