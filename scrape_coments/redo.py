urls = []
with open('urls.txt','r') as f:
    urls = f.readlines()

with open('urlss.txt','w') as f:
    for url in urls:
        if '2016' in url or '2015' in url:
            f.write(url)

