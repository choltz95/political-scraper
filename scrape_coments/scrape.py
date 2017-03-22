import fetchcomments
from tqdm import tqdm
import time
import random

scraped_urls = []
urls = []
print('reading urls...')
with open('urls.txt','r') as f:
    urls = f.readlines()
random.shuffle(urls) # shuffle url list

with open('scraped_urls.txt','r') as f:
    scraped_urls = f.readlines()

print('scraping comments...')
for i, url in enumerate(tqdm(urls)):
    if url in scraped_urls:
        continue
    url = url.strip()
    tqdm.write(url)
    data = fetchcomments.scrape(url)
    tqdm.write('comments: ' + str(len([comment for cursor in data for comment in cursor['response']])))
    if data != 2:
        scraped_urls.append(url)
    time.sleep(1)

print('writing scraped urls...')
with open('scraped_urls.txt','w') as f:
    for url in scraped_urls:
        url = url.strip()
        f.write(url + '\n')
