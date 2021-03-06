from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import sys
from datetime import datetime
import json
from selenium.webdriver.common.keys import Keys
from unidecode import unidecode
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
from collections import defaultdict


DATA_DIR = "C:/Users/igork/Data/"

BASE_URL = "http://pitchfork.com/reviews/albums/"

driver = webdriver.Chrome('webdriver/chromedriver')

# collect all album review URLs first

album_review_links = set()
reviews = []

REVIEWS_ON_PAGE = 12   # it's usually 12 but these are becoming visible dynamically, so often you can reach 24 on one page
WAIT_TIME = 30
pcount = 0


now = datetime.now()
year, month, day = now.year, now.month, now.day


while not driver.find_elements_by_class_name("end-infinite"):

    pcount += 1
    rcount = 0

    GOT_PAGE = False

    while not GOT_PAGE:
        try:
            """
            note that GET waits until the page has fully loaded (that is, the onload event has fired) 
            before returning control to your script
            """
            driver.get(BASE_URL + "?page=" + str(pcount))

            try:
                WebDriverWait(driver, WAIT_TIME).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "review-collection-fragment")))
                GOT_PAGE = True
            except:

                pass
            # try to get title
            # try:
            #     page_title = driver.find_element_by_xpath("//title")
            #     if page_title.text.strip().lower() == "502 bad gateway":
            #         print("encountered 502..")
            #         time.sleep(2)
            #     else:
            #         # if there's a title but not 502
            #         GOT_PAGE = True
            # except:
            #     GOT_PAGE = True
        except:
            print("problem with getting page...")
            print("retrying...")
            time.sleep(3)


    print("now on {}".format(driver.current_url))

    album_links_this_page = driver.find_elements_by_class_name("album-link")
    # print("found {} album links on this page".format(len(album_links_this_page)))

    for album in album_links_this_page:

        l = album.get_attribute("href")
        album_review_links.add(l)

    print("reviews so far: {}".format(len(album_review_links)))

driver.quit()

print("collected {} album links".format(len(album_review_links)))
print("requesting review pages...")

links_done = 0

for rl in album_review_links:

    GOT_PAGE = False

    while not GOT_PAGE:
        try:
            soup = BeautifulSoup(requests.get(rl, timeout=30).content, "lxml")
            GOT_PAGE = True
        except:
            print("requests couldn\'t get a page, retrying...")
            time.sleep(3)

    this_review = defaultdict()

    try:
        this_review["artist"] = unidecode(soup.find(class_='artists').text.strip().lower())
    except:
        this_review["artist"] = None
    try:
        this_review["album_title"] = unidecode(soup.find(class_='review-title').text.strip().lower())
    except:
        this_review["album_title"] = None
    try:
        this_review["review_date"] = unidecode(soup.find(class_='pub-date').text.strip())
    except:
        this_review["review_date"] = None
    try:
        this_review["pitchfork_score"] = unidecode(soup.find(class_='score-circle').text.strip())
    except:
        this_review["pitchfork_score"] = None
    try:
        this_review["review_abstract"] = unidecode(soup.find(class_='abstract').text.strip().lower())
    except:
        this_review["review_abstract"] = None
    try:
        this_review["review_text"] = unidecode(soup.find(class_='contents').text.strip().lower())
    except:
        this_review["review_text"] = None

    links_done += 1

    if (links_done % 50 == 0):
        print("processed reviews: {}/{} ({:.1f}%)".format(links_done, len(album_review_links), 100*links_done/len(album_review_links)))

    reviews.append(this_review)


print("saving reviews to json...")
json.dump(reviews, open("pitchfork_reviews_{:02d}{:02d}{:02d}.json".format(day, month, year), "w"))