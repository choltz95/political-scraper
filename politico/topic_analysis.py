import gensim
import csv
import json
import glob
from gensim import corpora, models
from collections import defaultdict
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


lda = gensim.models.LdaModel.load('topicModel')

for t in range(lda.num_topics):
    plt.figure()
    plt.imshow(WordCloud().fit_words(lda.show_topic(t, 200))) 
    plt.axis("off")
    plt.title("Topic #" + str(t))
    plt.savefig("topicClouds/topic"+str(t), bbox_inches='tight')
    plt.close() # close figure
