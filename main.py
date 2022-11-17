from airbnb import crawler
from airbnb import scraper
import json

def crawl():
    locations = [
        'Las Vegas, NV'
    ]
    urls = crawler.airbnb_crawl(keywords=locations)
    url_list = []
    for url in urls:
        if url not in url_list:
            url_list.append(url)
    with open('url.txt', 'w') as fout:
        fout.write('\n'.join(str(url) for url in url_list))
    fout.close()

def scrape():
    with open('url.txt', 'r') as fin:
        urls = [url.replace('\n', '') for url in fin.readlines()]
    fin.close()
    # urls = urls[0:10]
    data = scraper.airbnb_scrape(urls)
    with open('data.json', 'w') as fout:
        json.dump(data, fout, indent=2)
    fout.close()

if __name__ == '__main__':
    crawl()
    scrape()
    with open('data.json', 'r') as read_data:
        data = json.load(read_data)
    read_data.close()
    print(json.dumps(data, indent=2))