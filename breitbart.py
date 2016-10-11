# -*- coding: utf-8 -*-
import sys
import asyncio
import aiohttp
import multiprocessing as mp
from urllib.request import urlopen
import dateutil.parser as dateparse
from bs4 import BeautifulSoup
import tqdm
import json

topics = ["big-government","big-journalism", "big-hollywood", "national-security", "tech", "sports", "2016-presidential-race", "london", "jerusalem","texas", "california"]
articleids = [] # list of article ids we have seen

@asyncio.coroutine
def get(*args, **kwargs):
    """
    A wrapper method for aiohttp's get method.
    """
    try:
        response = yield from aiohttp.request('GET', *args, **kwargs)
        return (yield from response.text())
    except:
        return(1)
    
def get_articles_on_page(page, max_date):
    """
    Given the page extract the relevant text from it
    Want to multiprocess parsing step
    :param page: the page for the article list to scrape
    :param max_date: maximum date to scrape articles from
    :return: list of article dicts
    """
    soup = BeautifulSoup(page, "html5lib")
    a = soup.find_all('article')
    articles = []
    for article in a:
        try:
          if article['id'] not in articleids:
            date = article.find('span', {'class' : 'bydate'})
            if int(dateparse.parse(date.text).year) > max_date: # if we have not reached the max year yet continue
              adict = {}
              anchor = article.find('a')
              if anchor is not None:
                adict['title'] = anchor['title']
              adict['id'] = article['id']
              articleids.append(article['id'])
              adict['date'] = date.text
              adict['url'] = anchor['href']
              adict['content'] = get_text_from_article(anchor['href'])
              articles.append(adict)
            else: # break cycle if exceeds max year
              break
          else:
            continue
        except Exception as e:
          #print(str(e))
          continue
    return(articles)
    
@asyncio.coroutine
def get_articles(topic,pagenum, max_date=0):
  """
  Given a page number,
  download all article content for each article listed
  :param query: article list page number
  :return: list article dictionary objects
  """
  #url = 'http://www.breitbart.com/big-journalism/page/{}/'.format(query)
  url = 'http://www.breitbart.com/{}/page/{}/'.format(topic,pagenum)
  sem = asyncio.Semaphore(5) # at most 5 concurrent get requests
  with (yield from sem):
    page = yield from get(url, compress=True)
  if page != 1:
    articles = get_articles_on_page(page, max_date)
  else:
    pbar.update(100)
    return([])
  pbar.update(100)
  return(articles)

def get_text_from_article(url):
  """
  Given a url for an article
  parse article content
  :param url: the url for an article
  :return: string of article text
  """
  page = urlopen(url).read()
  soup = BeautifulSoup(page, "html5lib")
  articleText = ''
  for p in soup.find_all('p'):
    articleText = articleText+p.getText()
  return(articleText)

# year range
#y_start = sys.argv[1]
y_end = 0
if len(sys.argv) > 1:
  y_end = int(sys.argv[1])
  if len(sys.argv) > 2:
    num_cores = int(sys.argv[2])

num_pages = 2 # limit query to 200 pages ~ 3 years of articles
pbar = tqdm.tqdm(desc='Scraping pages',total=100*num_pages*len(topics)) # progress bar
loop = asyncio.get_event_loop()
f = asyncio.gather(*[get_articles(topic,pagenum,y_end) for topic in topics for pagenum in range(1,num_pages)])
data = loop.run_until_complete(f)
loop.close()
pbar.close()

data = [item for sublist in tqdm.tqdm(data,desc='Flattening') for item in sublist]

with open('output.json','w') as f:
  f.write(json.dumps(data))

with open('article_ids.txt','w') as f:
  for aid in articleids:
    f.write(aid + '\n')
