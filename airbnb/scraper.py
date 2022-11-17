from playwright.sync_api import sync_playwright
from playwright.sync_api import Page
from airbnb.settings import HEADLESS
import logging
import re

# Logger
logging.basicConfig(level=logging.DEBUG)

def airbnb_scrape(urls:list) -> list:
    """ Scrape Airbnb rental details """
    with sync_playwright() as p:
        # open browser
        browser = p.firefox.launch(headless=HEADLESS)
        page = browser.new_page()
        data = []
        for url in urls:
            # browse the website
            try:
                page.goto(url)
                logging.info(f"GET {url}")
            except Exception as e:
                logging.error(str(e))
            # parse website
            data.append(parse(page))
        # close browser
        browser.close()
    return data

def parse(page:Page) -> dict:
    """ Parse individual item page """
    # scrolling
    navigate_scroll(page)
    page.wait_for_load_state()

    # TITLE
    page.wait_for_selector('div[data-section-id=TITLE_DEFAULT]')
    section_title = page.query_selector('div[data-section-id=TITLE_DEFAULT]')
    title = section_title.query_selector('section > div > span > h1').inner_text()

    # LOCATION
    try:
        page.wait_for_selector('div[data-section-id=LOCATION_DEFAULT]')
        section_location = page.query_selector('div[data-section-id=LOCATION_DEFAULT]')
        if section_location.query_selector('h3') != None:
            location = section_location.query_selector('h3').inner_text().strip()
        else:
            location = section_location.query_selector_all('section > div')[1].inner_text().strip()
    except Exception as e:
        logging.warning(f"Failed to get LOCATION, message: {str(e)} ({page.url})")
    
    # REVIEWS - rating, reviews, specific rating: cleanliness, communication, check-in, accuracy, location, value
    reviews_detail = {}
    if page.locator('div[data-section-id=REVIEWS_DEFAULT]').count():
        section_reviews = page.query_selector('div[data-section-id=REVIEWS_DEFAULT]')
        # general rating - average rating, number of reviews
        try:
            text_reviews = section_reviews.query_selector('h2 > span').inner_text()
            rating = re.findall(r'\d{1}\.\d{1,2}', text_reviews)[0]
            reviews = re.findall(r'\d{1,}\sreviews?', text_reviews)[0]
            reviews_detail.update({
                'rating': float(rating),
                'reviews': int(reviews.replace('reviews', '').strip()),
            })
        except Exception as e:
            logging.warning(f'General REVIEWS is not properly parsed: {str(e)} ({page.url})')
        # specific rating - cleanliness, communication, check-in, accuracy, location, value
        rating_specific = section_reviews.query_selector('section > div > div > div')
        rating_specific = rating_specific.query_selector_all('div > div > div')
        rating_specific = [item.inner_text() for item in rating_specific]
        for item in rating_specific:
            if len(item.split('\n')) == 2:
                reviews_key = 'rating_' + item.split('\n')[0].strip().lower()
                reviews_val = item.split('\n')[1].strip()
                reviews_detail.update({
                    reviews_key: float(reviews_val)
                })
    elif page.locator('div[data-section-id=REVIEWS_EMPTY_DEFAULT]').count():
        reviews_detail.update({
            'rating': None,
            'reviews': None
        })
    else:
        logging.warning(f'Cannot found REVIEW section: {page.url}')
    # OVERVIEW / main facitities - number of guest, bedroom, bathroom
    facilities = {}
    try:
        page.wait_for_selector('div[data-section-id=OVERVIEW_DEFAULT]')
        section_facility_main = page.query_selector('div[data-section-id=OVERVIEW_DEFAULT]')
        facility_main = section_facility_main.query_selector_all('ol > li')
        for item in facility_main:
            facil = item.inner_text().replace('\u00b7', '').strip().split(' ')
            if len(facil) > 1:
                key = re.sub(r's$', '', facil[1].strip())
                value = int(facil[0].strip())
                facilities.update({key:value})
            elif len(facil) == 1 and facil[0].lower() == 'studio':
                key = 'studio'
                value = 1
                facilities.update({key:value})
            else:
                logging.warning(f"Main facilities have different format: {page.url}")
    except Exception as e:
        logging.error(f"Failed to get OVERVIEW: {str(e)} ({page.url})")
    
    # HOST PROFILE - host_name, is_verified, is_superhost, response_rate, response_time, host_languages
    host = {}
    try:
        page.wait_for_selector('div[data-section-id=HOST_PROFILE_DEFAULT]')
        section_host = page.query_selector('div[data-section-id=HOST_PROFILE_DEFAULT]')
        host_name = section_host.query_selector('h2').inner_text().replace('Hosted by','').strip()
        host_url = 'https://www.airbnb.com' + section_host.query_selector('section > div > div > div > a').get_attribute('href')
        host.update({
            'host_name': host_name,
            'host_url': host_url,
        })
        host.update({'is_verified': False, 'is_superhost': False})
        try:
            host_profile = section_host.query_selector_all('ul > li')
            host_profile = [item.inner_text() for item in host_profile]
            for item in host_profile:
                if len(item.split(':')) > 1:
                    # host response rate and time, maybe language
                    status_key = 'host_' + item.split(':')[0].strip().lower().replace(' ','_')
                    status_val = item.split(':')[1].strip()
                    host.update({status_key:status_val})
                elif item == 'Identity verified':
                    # host verification status
                    host.update({'is_verified':True})
                elif re.findall(r'Superhost', item):
                    # host badge status
                    host.update({'is_superhost':True})
                else:
                    #logging.debug(f'Host PROFILE - Passing item "{item}" ({page.url})')
                    continue
        except Exception as e:
            logging.warning(f'HOST PROFILE: {str(e)}')
    except Exception as e:
        logging.error(f'HOST PROFILE: {str(e)}')
    
    # PRICE - daily rate
    price = {}
    try:
        page.wait_for_selector('div[data-section-id=BOOK_IT_SIDEBAR]')
        section_booking = page.query_selector('div[data-section-id=BOOK_IT_SIDEBAR]')
        book_rate = section_booking.query_selector('div > div > span > span').inner_text()
        book_rate = book_rate.split('per')
        if len(book_rate) == 2:
            price.update({
                'daily_rate': float(book_rate[0].replace('$','').strip()),
                'currency': 'USD',
            })
        else:
            price.update({
                'daily_rate': book_rate[0],
                'currency': 'USD',
            })
    except Exception as e:
        logging.error(f'Failed to get BOOK: {str(e)} ({page.url})')
    
    # CALENDAR - minimum stay, amount of bookings per month
    calendar_info = {'days_booking_per_month': None, 'minimum_stay': None}
    # minimum stay
    page.query_selector('button[data-testid=homes-pdp-cta-btn]').click() # Check availability
    sidebar_popup = page.query_selector('div[data-testid=bookit-sidebar-availability-calendar]')
    day_range = sidebar_popup.query_selector('div[data-testid=availability-calendar-date-range]').inner_text()
    calendar_info.update({'minimum_stay': day_range})
    # amount of bookings per month
    try:
        page.wait_for_selector('div[data-section-id=AVAILABILITY_CALENDAR_INLINE]')
        container_calendar = page.query_selector('div[data-section-id=AVAILABILITY_CALENDAR_INLINE]')
        section_calendar = container_calendar.query_selector('div[aria-label=Calendar]')
        section_calendar = section_calendar.query_selector_all('div[data-visible=true]')
        days_booking_per_month = []
        for calendar in section_calendar:
            month = calendar.query_selector('h3').inner_text().strip()
            table = calendar.query_selector('table')
            rows = table.query_selector_all('tr')
            count_booked = 0
            for row in rows:
                date_button = row.query_selector_all('td[role=button]')
                for button in date_button:
                    button_value = button.get_attribute('aria-disabled')
                    if button_value == 'true':
                        date_booked = True # disabled=yes (grey date)
                    else:
                        date_booked = False # disabled=no
                    if date_booked:
                        count_booked += 1
            days_booking_per_month.append(f"{month} = {count_booked}")
            calendar_info.update({'days_booking_per_month': str(days_booking_per_month)})
    except Exception as e:
        logging.error(f'Failed to get CALENDAR: {str(e)} ({page.url})')
    
    # number of pictures
    pictures = {}
    page.locator('button', has_text='Show all photos').click()
    section_photos = page.query_selector('div[data-testid=photo-viewer-section]')
    n_pictures = len(section_photos.query_selector_all('picture'))
    pictures.update({'n_pictures': n_pictures})
    
    # great location rating
    # check in time
    # checkout time
    # cancellation policy
    # house rules - additional rules

    data = {
        'title': title,
        'location': location,
    }
    data.update(reviews_detail)
    data.update(price)
    data.update(pictures)
    data.update(calendar_info)
    data.update(facilities)
    data.update(host)
    data.update({'url': page.url.split('?')[0]})
    return data

def navigate_scroll(page:Page, x=5, timeout=3000) -> None:
    """ Page scroll to get all the content of product page rendered
    Positive x is scrolling down, negative x is scrolling up
    """
    a = 1 if x >= 0 else -1
    # logging.debug(f"Scrolling screen...")
    for i in range((x * a)): # make the range as long as needed
        page.mouse.wheel(0, 15000) # h=0, v=15000
        page.wait_for_timeout(timeout)
        i += 1
    return

if __name__ == '__main__':
    pass