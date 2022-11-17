from playwright.sync_api import sync_playwright
from playwright.sync_api import Page
from airbnb.settings import HEADLESS
import logging

logger = logging.getLogger('crawler')

def airbnb_crawl(keywords:list) -> list:
    """ Crawl Airbnb by rental location """
    with sync_playwright() as p:
        # open browser
        browser = p.firefox.launch(headless=HEADLESS)
        page = browser.new_page()
        # browse the website
        try:
            navigate_home(page)
            page.wait_for_load_state()
            # close popup if appears
            try:
                page.wait_for_selector('div[aria-labelledby=announcement-curtain]')
                page.locator('button[aria-label=Close]').click()
                logger.info('Popup closed')
            except:
                logger.info('No pop-up in current session')
        except Exception as e:
            logger.error(f"Failed to navigate Airbnb home.{str(e)}")
        # location handle
        item_links = []
        for query in keywords:
            navigate_location(query, page)
            page.wait_for_selector('div[itemprop=itemListElement]')
            page.wait_for_timeout(6500)
            item_links += get_item_links(page)
            logger.info(f"Page {get_page_number(page)} of {query}")
            # pagination handle
            while is_visible_nexpage(page):
                navigate_nextpage(page)
                page.wait_for_selector('div[itemprop=itemListElement]')
                page.wait_for_timeout(6500)
                item_links += get_item_links(page)
                logger.info(f"Page {get_page_number(page)} of {query}")
        # close browser
        browser.close()
    return item_links

def navigate_home(page:Page) -> None:
    """ Navigate to Airbnb home website """
    page.goto('https://www.airbnb.com', timeout=150000)
    page.wait_for_load_state()
    return

def navigate_location(query_location:str, page:Page) -> None:
    """ Navigate Airbnb web using query location """
    # click search bar
    page.locator('button', has_text='Location').click()
    # input query
    page.wait_for_selector('input#bigsearch-query-location-input', timeout=10000)
    page.fill('input[placeholder="Search destinations"]', query_location)
    # click search button
    page.locator('button').get_by_text('Search').click()
    logger.info(f'Navigate to {query_location} rentals...')
    page.wait_for_load_state()
    return

def is_visible_nexpage(page:Page) -> bool:
    """ Next page appearance check """
    if page.query_selector('a[aria-label=Next]') != None:
        return True
    else:
        return False

def navigate_nextpage(page:Page) -> None:
    """ Navigate to the next page """
    endpoint = page.query_selector('a[aria-label=Next]').get_attribute('href')
    url = 'https://www.airbnb.com' + endpoint
    page.goto(url, timeout=90000)
    return

def get_page_number(page:Page) -> int:
    """ Number from active pagination """
    return int(page.query_selector('button[aria-current=page]').inner_text())

def get_item_links(page:Page) -> list:
    """ Get link to the rentals from search page """
    items = page.query_selector_all('a[aria-labelledby*=title_]')
    links = ['https://www.airbnb.com' + item.get_attribute('href').split('?')[0] for item in items]
    return links

if __name__ == '__main__':
    pass
