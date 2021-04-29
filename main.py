#!/usr/bin/env python3

from sys import exit
import requests
from datetime import datetime
import uuid

SESSION_ID=uuid.uuid4().hex
START_TIME=datetime.now()
LOADING_ANIMATION=['|', '/', '-', '\\']

PAGESIZE = 100
SEARCH_TYPE='product'
URL='https://www.vinmonopolet.no/api'
SEARCH_URL='{}/search?q=:relevance:visibleInSearch:true&searchType={}&pageSize={}&currentPage='.format(URL, SEARCH_TYPE, PAGESIZE)
PRODUCT_URL='{}/products'.format(URL)

ELASTIC_URL='http://localhost:9200'
WINE_INDEX='{}/wines-{}'.format(ELASTIC_URL, START_TIME.strftime("%Y.%m.%d"))

CURRENT_PAGE=0
TOTAL_PAGES=-1

elasticIndexedWineIds = 0

class ElasticNotFound(Exception):
  def __init__(self):
    self.message = 'Elastic not available at: {}'.format(ELASTIC_URL)
    super().__init__(self.message)

def checkElastic():
  try:
    r = requests.get(ELASTIC_URL)
    if r.status_code != 200: raise ElasticNotFound
    return
  except:
    raise ElasticNotFound

def addWineToElastic(wine):
  global elasticIndexedWineIds

  url = '{}/_doc'.format(WINE_INDEX)
  data = {
    "@timestamp": str(datetime.now().isoformat()),
    "wine": wine,
    "session_id": SESSION_ID,
    "search_type": SEARCH_TYPE,
    "current_page": CURRENT_PAGE,
    "total_pages": TOTAL_PAGES,
    "batch_size": PAGESIZE
  }

  r = requests.post(url, json=data)
  wineInsertResponse = r.json()
  result = wineInsertResponse['result']
  if (result != "created"):
    print('Error! from elastic wine insert:')
    print(wineInsertResponse.json())
  else:
    elasticIndexedWineIds += 1


def fetchWine(wineId):
  url = '{}/{}/?fields=FULL'.format(PRODUCT_URL, wineId)
  wineResponse = requests.get(url)
  wine = wineResponse.json()
  addWineToElastic(wine)

def fetchPage(page):
  global TOTAL_PAGES

  print('\nSearching products at page {}/{}'.format(page, TOTAL_PAGES if TOTAL_PAGES > 0 else '?' ))
  url = '{}{}'.format(SEARCH_URL, page)
  r = requests.get(url)
  results = r.json()

  productResults = results['productSearchResult']
  currentPage = productResults['pagination']['currentPage']
  if (TOTAL_PAGES == -1):
    TOTAL_PAGES = productResults['pagination']['totalPages']

  products = productResults['products']
  print('Search found {} products'.format(len(products)))

  start = datetime.now()
  frame = 0
  for index, product in enumerate(products):
    fetchWine(product['code'])
    print(' {} Indexed {} of {} products'
      .format(LOADING_ANIMATION[frame], index+1, len(products)), end='\r')
    frame += 1
    if (frame == len(LOADING_ANIMATION)):
      frame = 0

  end = datetime.now()
  print('Finised adding {} wines to elastic index'.format(len(products)))
  print('Total products indexed: {}'.format(elasticIndexedWineIds))
  print('It took: {}, total time: {}'.format(end - start, end - START_TIME))

def main():
  global CURRENT_PAGE, TOTAL_PAGES

  while CURRENT_PAGE < TOTAL_PAGES or TOTAL_PAGES is -1:
    fetchPage(CURRENT_PAGE)
    CURRENT_PAGE += 1

  print('Total wines added to elastic: {}'.format(elasticIndexedWineIds))

if __name__ == '__main__':
  try:
    checkElastic()
    main()
  except KeyboardInterrupt:
    print('\n\nKeyboard interrupt.. exiting!')
    print('Was at page {} of {}. Total indexed products where: {}'.format(CURRENT_PAGE, TOTAL_PAGES, elasticIndexedWineIds))
    exit(0)
