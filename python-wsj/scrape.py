import re
import sys
import time
from bs4 import BeautifulSoup
import json
import datetime
from selenium import webdriver

#===============================================================================
## firefox profile - remove some rendering to speed up automation with quickjava extension
firefox_profile = webdriver.FirefoxProfile()
firefox_profile.add_extension("quickjava-2.1.2-fx.xpi")
firefox_profile.set_preference("thatoneguydotnet.QuickJava.curVersion", "2.0.6.1") # Prevents loading the 'thank you for installing screen'
firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.Images", 2) # Turns images off
firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.AnimatedImage", 2) # Turns animated images off
#firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.CSS", 2) # CSS
firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.Flash", 2) # Flash
firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.Java", 2) # Java
firefox_profile.set_preference("thatoneguydotnet.QuickJava.startupStatus.Silverlight", 2) # Silverlight
#===============================================================================

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

## Loading URL
extractItems = []
browser = webdriver.Firefox(firefox_profile)
browser.get('http://markets.wsj.com/?mod=Homecle_MDW_MDC')

# ==============================================================================
## Login Credentials
login = browser.find_element_by_link_text("Log In").click()
loginID = browser.find_element_by_id("username").send_keys('')  # Input username
loginPass = browser.find_element_by_id("password").send_keys('')     # Input password
loginReady = browser.find_element_by_class_name("login_submit")
loginReady.submit()
# ==============================================================================

time.sleep(2.5)

search_box = browser.find_element_by_id("globalHatSearchInput")
search_box.send_keys('trump')                                                   # Input search keyword
search_req = browser.find_element_by_css_selector('.button-search').click()
toggleMenu = browser.find_element_by_link_text("ADVANCED SEARCH")
toggleMenu.click()
menuOptions = browser.find_element_by_class_name('datePeriod')
toggleButton = menuOptions.find_element_by_css_selector(".dropdown-toggle")
toggleButton.click()
dropdownOptions = menuOptions.find_elements_by_tag_name("li")
dropdownOptions[len(dropdownOptions)-1].click()                                 # Adjust list length for date ranges
searchArchive = browser.find_element_by_class_name('keywordSearchBar')
searchArchive.find_element_by_class_name("searchButton").click()

print('search in progress..')

articles = []

def getPageUrl(elementLinks):
    extractLinks = []
    for element in elementLinks:
        links = element.get_attribute('href')
        if links is not None:
	    extractLinks.append(links)
    return(extractLinks)

def extractElements(url):
    #second_browser = webdriver.Firefox()
    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 't')
    for extracted_url in getPageUrl(elementLinks):
        #second_browser.get(extracted_url)
	browser.get(extracted_url)
        page = browser.page_source
        soup = BeautifulSoup(page,"html5lib")
         
        article = {}
        try:
	    article['id'] = soup.find('meta',{'name':'article.id'}).get('content')
	    article['title'] = soup.find('meta',{'name':'article.headline'}).get('content')
	    article['author'] = soup.find('meta',{'name':'author'}).get('content')
	except:
            continue 
	try:
	    article['date'] = soup.find('meta',{'name':'article.published'}).get('content')
	    
	    article['tags'] = soup.find('meta',{'name':'keywords'}).get('content').split(',')
	except:
	    pass

	article['url'] = extracted_url
        article['content'] = ''
      
        try:
            parent = soup.find('article',{'id':'article-contents'}) 
        except AttributeError:
            try:
                parent = soup.find('div',{'id':'article_sector'})
            except AttributeError:
                pass

        try:
            paragraphs = parent.find_all('p')
        except:
            continue

        article_text = ''
        for p in paragraphs:
            article_text = article_text + p.getText().strip()
        
        article['content'] = article_text
   
        articles.append(article)
	time.sleep(2.5)
    #second_browser.close()
    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
    time.sleep(2.5)

# Start iterating links in search results
i = 0
while True:
    if i % 10 == 0:
        print('page: ' + str(i))
    if len(articles) > 0:
        with open('data/'+str(datetime.datetime.now()).replace(' ','')+'.txt','w') as f:
            f.write(json.dumps(articles))
    try:
        browser.find_element_by_class_name('next-page')
        
        elementLinks = browser.find_elements_by_xpath('//h3[@class="headline"]/a')
        extractElements(getPageUrl(elementLinks))
        
        element = browser.find_element_by_link_text('Next')
        element.click()
        i = i + 1
    except Exception as e:
	print('some issue lol...')
        browser.close()
	print(e)
	break


