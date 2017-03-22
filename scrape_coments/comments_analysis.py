import os
import json

comments = []

for filename in os.listdir('data/'):
    if filename.endswith('.json'):
        with open('data/' + filename) as f:
            data = json.load(f)
        comments = [comment for cursor in data for comment in cursor['response']]
        print len(comments)
        #print data[0]['response'][0]
