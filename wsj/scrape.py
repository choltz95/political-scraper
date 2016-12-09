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
    
def get_articles_on_page(page,date, max_date):
    """
    Given the page extract the relevant text from it
    Want to multiprocess parsing step
    :param page: the page for the article list to scrape
    :param max_date: maximum date to scrape articles from
    :return: list of article dicts
    """
    soup = BeautifulSoup(page, "html5lib")
    archivedArticles = soup.find('div',{'id':'archivedArticles'})
    articleList = archivedArticles.find('ul',{'class':'newsItem'})
    a = articleList.find_all('li')
    articles = []
    for article in a: 
        try:
          summary = article.find('p').text
          url = article.find('a')['href'] # need to get url and aid from url in advance
          aid = url.split('-')[-1]
          if aid not in articleids:
              adict = {}
              adict['id'] = aid
              articleids.append(aid)
              adict['title'] = article.find('a').text
              d = dateparse.parse(str(date[0])+'-'+str(date[1])+'-'+str(date[2]))
              adict['date'] = d.strftime("%d %B %Y")
              adict['url'] = url
              article_content = get_text_from_article(url) 
              adict['author'] = article_content[0]
              adict['content'] = article_content[1]
              adict['tags'] = article_content[2]
              articles.append(adict) 
              stime = uniform(.5,1) # randomize sleep times
              sleep(stime) # sleep between article requests
          else:
              #sleep(2)
              continue
        except Exception as e:
          errs.append('[ART]: '+str(e))
          continue
    return(articles)
    
@asyncio.coroutine
def get_articles(date,sem,max_date=0):
  """
  Given a page number,
  download all article content for each article listed
  :param query: article list page number
  :return: list article dictionary objects
  """
  url = 'http://www.wsj.com/public/page/archive-{}-{}-{}.html'.format(date[0],date[1],date[2])
  with (yield from sem):
    page = yield from get(url, compress=True)
  if page != 1:
    articles = get_articles_on_page(page, date, max_date)
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
  #content = soup.find('article') # need to figure out how to log in
  #paragraphs = content.find_all('p')
  author = soup.find('meta',{'name':'author'}).get('content')
  tags = soup.find('meta',{'name':'keywords'}).get('content').split(',')

  #for p in paragraphs:
  #    articleText = articleText+p.getText().strip()
  return(author,articleText,tags)

def daterange(start_date, end_date):
    dr  =[]
    for n in range(int ((end_date - start_date).days)):
        dr.append(start_date + datetime.timedelta(n))
    return dr

start_date = datetime.date(2016,11,13) # 2011 1 1
end_date = datetime.date(2016, 11,14)
date_range = daterange(start_date, end_date)

y_end = 0
if len(sys.argv) > 1:
  y_end = int(sys.argv[1])
  if len(sys.argv) > 2:
    num_cores = int(sys.argv[2])

with open('article_ids.txt','r') as f:
  for i_d in f:
    articleids.append(i_d.rstrip())

sem = asyncio.Semaphore(10) # at most n concurrent get requests
pbar = tqdm.tqdm(desc='Scraping pages',total=100*len(date_range)) # progress bar
loop = asyncio.get_event_loop()
f = asyncio.gather(*[get_articles(tuple(date.timetuple()),sem) for date in date_range])
data = loop.run_until_complete(f)
loop.close()
pbar.close()


data = [item for sublist in tqdm.tqdm(data,desc='Flattening') for item in sublist] # flatten async queue
print(str(len(data)) + ' articles saved')

if len(data) > 0:
  with open('data/'+str(datetime.datetime.now()).replace(' ','')+'.txt','w') as f:
    f.write(json.dumps(data)) 

#with open('article_ids.txt','w') as f:
#  for aid in articleids:
#    f.write(aid + '\n')

with open('log.txt','w') as f:
  for err in errs:
    if err.strip() != "":
      f.write(err + '\n')

