import sys, os
sys.path.append(os.path.abspath(os.path.pardir))

from airbnb import scraper
from logging import config

config.fileConfig(fname='../config.conf', disable_existing_loggers=False)

with open('urls.txt', 'r') as fin:
    urls = [url.replace('\n', '') for url in fin.readlines()]
fin.close()
scraper.airbnb_scrape(urls)

