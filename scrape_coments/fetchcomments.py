import urllib, json
import sys
import time

disqus = "http://disqus.com/api/3.0/posts/list.json"

def makeURL(base, key, forum, thread, cursor=None):
  url = "%s?api_key=%s&forum=%s&thread=%s" % (base, key, forum, thread)
  if cursor:
    url = "%s&cursor=%s" % (cursor)
  return url

def getJSON(url):
  resp = urllib.urlopen(url)
  data = json.loads(resp.read())
  return data

def getNext(data):
  if data and data.has_key("cursor"):
    cursor = data["cursor"]
    if cursor.has_key("hasNext"):
        if cursor["hasNext"] == False:
            return None
        else:
            if cursor.has_key("next"):
              return cursor["next"]
  return None

def verify_thread(data):
    i = 0
    ids = set()
    try: # bad
        for comment in data['response']:
            ids.add(comment['thread'])
        if len(ids) > 1:
            print('[DEBUG] verify_thread - no thread')
            return 1
        else:
            return 0
    except:
        print('[DEBUG] verify_thread - rate limit')
        return -1

def scrape(url):
    api_key = open("api_key.txt").read().strip()
    forum = "breitbartproduction"
    #thread = "link:http://www.breitbart.com/tech/2016/11/12/report-university-of-pennsylvania-offers-puppies-coloring-books-to-students-distraught-over-trump-win/"
    thread_url = url
    thread = 'link:'+thread_url
    comments = []
    url = makeURL(disqus, api_key, forum, thread)
    data = getJSON(url)
    hops = 0

    comments.append(data)
    while data and hops < 800: 
      v = verify_thread(data)
      if v == 1:
        return 1
      elif v == -1:
        print('ratelimit exceeded on: ' + url)
        time.sleep(3000) # wait hour to reset rate limit
        return 2
      nextPage = getNext(data)
      #print nextPage
      if nextPage:
        url2 = "%s&cursor=%s" % (url, nextPage)
        data = getJSON(url2)
        comments.append(data)
      else:
        break
      hops += 1
      time.sleep(4)
    with open('./data/'+thread_url.replace('/','_')+'.json','w') as f:
        json.dump(comments,f,indent=2)
    return comments
