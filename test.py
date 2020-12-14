import logging
from pprint import pprint

import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

from owmeta_modeldb import scrape, scrape_file


logging.basicConfig(level=logging.DEBUG)

base_session = requests.Session()
http_cache = FileCache('.http_cache')
session = CacheControl(base_session, cache=http_cache)
#pprint(scrape(229585, session))
pprint(scrape('http://modeldb.yale.edu/266842', session))
# with open('ModelDB A detailed Purkinje cell model (Masoli et al 2015).html', 'rb') as f:
    # pprint(scrape_file(f))
