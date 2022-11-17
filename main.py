from airbnb import crawler
from airbnb import scraper
import json

def crawl(locations:list, output_file:str) -> None:
    urls = crawler.airbnb_crawl(keywords=locations)
    url_list = []
    for url in urls:
        if url not in url_list:
            url_list.append(url)
    with open(output_file, 'w') as fout:
        fout.write('\n'.join(str(url) for url in url_list))
    fout.close()
    return

def scrape(input_file:str, output_file:str):
    with open(input_file, 'r') as fin:
        urls = [url.replace('\n', '') for url in fin.readlines()]
    fin.close()
    # urls = urls[0:10]
    data = scraper.airbnb_scrape(urls)
    with open(output_file, 'w') as fout:
        json.dump(data, fout)
    fout.close()

def print_result(data_file:str):
    with open(data_file, 'r') as read_data:
        data = json.load(read_data)
    read_data.close()
    return print(json.dumps(data, indent=2))

if __name__ == '__main__':
    locations = [
        'Las Vegas, NV'
    ]
    crawl(locations, output_file='url.txt')
    scrape(input_file='url.txt', output_file='data.json')
    print_result('data.json')