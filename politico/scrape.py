# -*- coding: utf-8 -*-
import re
import sys
import asyncio
import aiohttp
from urllib.request import urlopen
import dateutil.parser as dateparse
from bs4 import BeautifulSoup
import tqdm
import json
from time import sleep
import datetime
from random import uniform

errs = [] # error-log list
articleids = [] # list of article ids we have seen

@asyncio.coroutine
def get(*args,n=0, **kwargs): # recursive n details how many times we have attempted this get.
    """
    A wrapper method for aiohttp's get method.
    """
    if n > 10:
      return(1)
    try:
      response = yield from aiohttp.request('GET', *args, **kwargs)
      return (yield from response.text())
    except Exception as e: # except non http-200 responses
      errs.append('[GET]: ' + str(e))
      if str(503) in str(e):
        print('[http] 503')
      #  sleep(200) # sleep longer
      #  response = yield from aiohttp.request('GET',*args,**kwargs,n++)
      #  return (yield from response.text())
      #else:
        #errs.append('[GET(failed)]: ' + str(e))
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
    [tag.decompose() for tag in soup.find_all('aside')]
    [tag.decompose() for tag in soup.find_all('section', {'class': 'latest-news'})]
    [tag.decompose() for tag in soup.find_all('div',{'class': 'quick-story'})]
    a = soup.find_all('article')
    articles = []
    for article in a: 
        try:
          summary = article.find('div', {'class':'summary'})
          header = summary.find('header')
          footer = summary.find('footer')
          url = header.find('a')['href'] # need to get url and aid from url in advance
          aid = url.split('-')[-1]
          if 'video' not in url and aid not in articleids:
            date = summary.find('time')
            if int(dateparse.parse(date.text).year) > max_date: # if we have not reached the max year yet continue
              adict = {}
              adict['id'] = aid
              articleids.append(aid)
              adict['title'] = header.find('a').text
              adict['date'] = date.text
              adict['url'] = url
              article_content = get_text_from_article(url) 
              adict['author'] = article_content[0]
              adict['content'] = article_content[1]
              adict['tags'] = article_content[2]
              articles.append(adict) 
              stime = uniform(.5,1) # randomize sleep times
              sleep(stime) # sleep between article requests
            else: # break cycle if exceeds max year
              break
          else:
            #sleep(2)
            continue
        except Exception as e:
          errs.append('[ART]: '+str(e))
          continue
    return(articles)
    
@asyncio.coroutine
def get_articles(topic,pagenum,sem,max_date=0):
  """
  Given a page number,
  download all article content for each article listed
  :param query: article list page number
  :return: list article dictionary objects
  """
  url = 'http://www.politico.com/search/{}?s=newest&adv=true'.format(pagenum)
  with (yield from sem):
    page = yield from get(url, compress=True)
  if page != 1:
    articles = get_articles_on_page(page, max_date)
  else:
    pbar.update(100)
    sleep(2)
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
  author = ''
  tags = []
  [tag.decompose() for tag in soup.find_all('div', {'class': 'promo'})]
  [tag.decompose() for tag in soup.find_all('figcaption')]
  js = soup.find('body',{'class' : 'template-story'}).find('script',{'type':'text/javascript'}).text
  content = soup.find_all('p')
  author = ''.join(re.findall('\"content_author\":\"(.*?)\"', js, re.DOTALL))
  tags = ''.join(re.findall('\"content_tag\":\"(.*?)\"', js, re.DOTALL)).split('|')
  for p in content:
    cl = p.get('class')
    ig = ["story-continued", "block-label", "subtitle", "byline", "subhead", "copyright"]
    if cl is None:
      articleText = articleText+p.getText().strip()
  return(author,articleText,tags)

topics = ['']

# year range
y_end = 0
if len(sys.argv) > 1:
  y_end = int(sys.argv[1])
  if len(sys.argv) > 2:
    num_cores = int(sys.argv[2])

with open('article_ids.txt','r') as f:
  for i_d in f:
    articleids.append(i_d.rstrip())

page_start = 14000
num_pages =  14200# limit query
sem = asyncio.Semaphore(10) # at most n concurrent get requests
pbar = tqdm.tqdm(desc='Scraping pages',total=100*(num_pages - page_start)) # progress bar
loop = asyncio.get_event_loop()
f = asyncio.gather(*[get_articles(topic,pagenum,sem,y_end) for topic in topics for pagenum in range(page_start,num_pages)])
data = loop.run_until_complete(f)
loop.close()
pbar.close()

data = [item for sublist in tqdm.tqdm(data,desc='Flattening') for item in sublist] # flatten async queue
print(str(len(data)) + ' articles saved')

if len(data) > 0:
  with open('data/'+str(datetime.datetime.now()).replace(' ','')+'.txt','w') as f:
    f.write(json.dumps(data)) 

with open('article_ids.txt','w') as f:
  for aid in articleids:
    f.write(aid + '\n')

with open('log.txt','w') as f:
  for err in errs:
    if err.strip() != "":
      f.write(err + '\n')

