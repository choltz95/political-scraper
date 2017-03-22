import fetchcomments
from tqdm import tqdm

scraped_urls = []
urls = []
print('reading urls...')
with open('urls.txt','r') as f:
    urls = f.readlines()
with open('scraped_urls.txt','r') as f:
    scraped_urls = f.readlines()

print('scraping comments...')
for i, url in enumerate(tqdm(urls)):
    print url.strip()
    if url in scraped_urls:
        continue
    if i == 1:
        break
    url = url.strip()
    data = fetchcomments.scrape(url)
    tqdm.write(str(len(data)))
    scraped_urls.append(url)

#print('writing scraped urls...')
#with open('scraped_urls.txt','w') as f:
#    for url in scraped_urls:
#        f.write(url + '\n')
