import sys, os
sys.path.append(os.path.abspath(os.path.pardir))

from airbnb import crawler
from logging import config

config.fileConfig(fname='../config.conf', disable_existing_loggers=False)
crawler.airbnb_crawl(['Los Angeles, CA', 'Las Vegas, NV'])
