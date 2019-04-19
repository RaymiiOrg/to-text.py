#!/usr/bin/env python2
# Author: Remy van Elst <raymii.org>
# License: GNU GPLv2

# pip install html2text requests readability-lxml feedparser
import requests
from readability import Document
import html2text
import argparse 
import feedparser
import sys
import time
import re
import os
from datetime import datetime
from time import mktime
from urlparse import urlparse

parser = argparse.ArgumentParser(description='Convert HTML page to text using readability and html2text.')
parser.add_argument('-u','--url', help='URL to convert', required=True)
parser.add_argument('-s','--sleep', help='Sleep X seconds between URLs (only in rss)', default=3)
parser.add_argument('-r', '--rss', help="URL is RSS feed. Parse every item in feed", 
    default=False, action="store_true")
parser.add_argument('-n', '--noprint', help="Dont print converted contents", 
    default=False, action="store_true")
parser.add_argument('-o', '--original', help="Dont parse contents with readability.", 
    default=False, action="store_true")
args = vars(parser.parse_args())

def cookie_workaround_ad(url):
    hostname = urlparse(url).hostname
    if hostname == "ad.nl" or hostname == "www.ad.nl":
        url = "https://www.ad.nl/accept?url=" + url
    return url

def cookie_workaround_tweakers(url):
    hostname = urlparse(url).hostname
    if hostname == "tweakers.net" or hostname == "www.tweakers.net":
        headers['X-Cookies-Accepted'] = '1'

def cookie_workaround_rd(url):
    hostname = urlparse(url).hostname
    if hostname == "rd.nl" or hostname == "www.rd.nl":
        headers['cookieInfoV4'] = "1"

def cookie_workaround_geenstijl(url):
    hostname = urlparse(url).hostname
    if hostname == "geenstijl.nl" or hostname == "www.geenstijl.nl":
        headers['Cookie'] = "cpc=10"

def cookie_workarounds_url(url):
    url = cookie_workaround_ad(url)
    return url

def cookie_workarounds_header(url):
    cookie_workaround_tweakers(url)
    cookie_workaround_rd(url)
    cookie_workaround_geenstijl(url)

def get_url(url):
    url = cookie_workarounds_url(url)
    cookie_workarounds_header(url)
    return requests.get(url, headers=headers, timeout=5)

def convert_doc(html_text):
    return Document(input=html_text, 
        positive_keywords=["articleColumn", "article", "content", 
        "category_news"],
        negative_keywords=["commentColumn", "comment", "comments", 
        "posting_list reply", "posting reply", "reply"])


def convert_doc_to_text(doc_summary):
    doc = html2text.html2text(doc_summary).encode('utf-8').strip()
    if len(doc) > 0:
        return doc
    else:
        return "parsing failed."

def save_doc(text, title, url, rssDate=0):
    hostname = urlparse(url).hostname
    if not os.path.exists("saved/" + hostname):
        os.makedirs("saved/" + hostname)
    filename = re.sub(r'[^A-Za-z]', '_', title)
    if rssDate:
        posttime = datetime.fromtimestamp(mktime(rssDate)).strftime("%Y%m%dT%H%M")
    else:
        posttime = datetime.now().strftime("%Y%m%dT%H%M")
    filename = "saved/" + hostname + "/" + posttime + "_" + filename + ".txt"
    if not os.path.exists(filename):
        with open(filename, "w") as textfile:
            textfile.write("# " + title)
            textfile.write("\nSource URL: \t" + url)
            textfile.write("\nDate: \t\t" + posttime)
            textfile.write("\n\n")
            textfile.write(text)  
    return filename

headers = {'User-Agent': 'Tiny Tiny RSS/19.2 (1a484ec) (http://tt-rss.org/)'} 

response = get_url(args['url'])

if args['rss']:
    feed = feedparser.parse(response.text)
    if feed.bozo:
        print("Invalid XML.")
        sys.exit(1)
    else:
        for post in feed.entries:
            response = get_url(post['link'])
            doc = convert_doc(response.text)
            if args['original']:
                text = convert_doc_to_text(doc.content())
            else:
                text = convert_doc_to_text(doc.summary())
            title = doc.short_title().encode('utf-8').strip()
            filename = save_doc(text, title, post['link'], post['published_parsed'])
            if not args['noprint']:
                print("\n\n========================\n\n") 
                print("# " + title)
                print("Source URL: " + post['link'])
                print("\n")
                print(text)
                print("file saved as " + filename)
            if args['sleep']:
                time.sleep(args['sleep'])
else:
    doc = convert_doc(response.text)
    if args['original']:
        text = convert_doc_to_text(doc.content())
    else:
        text = convert_doc_to_text(doc.summary())
    title = doc.short_title().encode('utf-8').strip()
    filename = save_doc(text, title, args['url'])
    if not args['noprint']:
        print("\n\n========================\n\n") 
        print("# " + title)
        print("Source URL: " + args['url'])
        print("\n")
        print(text)
        print("file saved as " + filename)