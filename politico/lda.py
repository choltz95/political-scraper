import gensim
import csv
import json
import glob
from gensim import corpora, models
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from time import gmtime, strftime
from collections import defaultdict

tokenizer = RegexpTokenizer(r'\w+')
lem = WordNetLemmatizer()
cachedStopWords = set(stopwords.words("english"))
body = []
processed = []

with open("politico_data.json", "r") as f:
    d = json.load(f)

for i in range(0,len(d)):
    body.append(d[i]['content'].lower())

for entry in body:
    frequency = defaultdict(int)
    text = tokenizer.tokenize(entry)
    for token in text:
        frequency[token] += 1
    processed.append([lem.lemmatize(word) for word in text if word not in cachedStopWords and frequency[word]>1 and len(lem.lemmatize(word))>1])

dictionary = corpora.Dictionary(processed)
corpus = [dictionary.doc2bow(text) for text in processed]
lda = gensim.models.ldamulticore.LdaMulticore(corpus, id2word=dictionary, num_topics=50, passes=1, workers=4)
lda.save('topicModel')
topics = lda.show_topics(num_topics=50, num_words=16)
#print topics
ttopics = lda.top_topics(corpus, num_words=16)

with open('ttopics.txt','w') as f:
    for topic in ttopics:
        f.write(str(topic)+'\n')

with open('stopics.txt','w') as f:
    for topic in topics:
        f.write(str(topic)+'\n')
