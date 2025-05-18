import os
from urllib.parse import urljoin, urlparse
import mimetypes

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import requests
from seleniumwire import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re

# Define common browser headers to mimic a real browser request
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

options = Options()
# options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--blink-settings=imagesEnabled=false")
options.add_argument(f"user-agent={BROWSER_HEADERS['User-Agent']}")
options.page_load_strategy = 'eager'
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(7)
failed_websites = []

os.makedirs("../data/logos", exist_ok=True)
os.makedirs("../data/logos/pngs", exist_ok=True)
os.makedirs("../data/logos/svgs", exist_ok=True)
df = pd.read_parquet('../data/logos.snappy.parquet')
img_src = ''
stats = {
    'logo': 0,
    'website': 0,
    'offline': 0,
    'percentage': None
}


def stats_build(logo, website, offline, stats):
    stats['logo'] += logo
    stats['website'] += website
    stats['offline'] += offline
    if stats['website'] - stats['offline'] > 0:
        stats['percentage'] = stats['logo'] / (stats['website'] - stats['offline']) * 100
    else:
        stats['percentage'] = 0.0
    print("Logos extracted: " + str(stats['logo']) +
          " | Websites checked: " + str(stats['website']) +
          " | Offline websites: " + str(stats['offline']) +
          " | Success percentage: {:.2f}%".format(stats['percentage']))
    return stats


def save_image(url, stats, response):
    # Check if the response is valid before saving
    if response.status_code != 200:
        print(f"Invalid response status code {response.status_code} for URL: {url}")
        return False

    # Check if the content is an HTML error page
    content_type = response.headers.get('Content-Type', '').lower()
    if 'text/html' in content_type and any(error_text in response.text for error_text in
                                           ['403 ERROR', '404 ERROR', 'ERROR: The request could not be satisfied']):
        print(f"Error page detected in response from URL: {url}")
        return False

    path = f"../data/logos/pngs/logo{stats['logo']}"
    if url.lower().endswith('.svg') or 'svg' in content_type or \
            '<svg' in response.content[:100].decode('utf-8', errors='ignore').lower():
        path = f"../data/logos/svgs/logo{stats['logo']}"
        with open(f"{path}.svg", "w", encoding="utf-8") as f:
            f.write(response.text)
        stats_build(1, 0, 0, stats)
        print(f"SVG salvat din URL-ul: {url}")
        return True

    # For binary image formats like PNG, check content type
    if not ('image/png' in content_type or 'image/jpeg' in content_type or 'image/gif' in content_type):
        print(f"Invalid content type {content_type} for URL: {url}")
        return False

    with open(f"{path}.png", "wb") as f:
        f.write(response.content)
    stats_build(1, 0, 0, stats)
    print(f"PNG salvat din URL-ul: {url}")
    return True


def try_selenium_search_all_img_or_svg(driver, stats, response):
    logo_elements = driver.find_elements(By.XPATH,
                                         "//img[" +
                                         "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or " +
                                         "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or " +
                                         "contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or " +
                                         "contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand')" +
                                         "] | " +
                                         "//svg[" +
                                         "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                         "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or " +
                                         "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                         " 'abcdefghijklmnopqrstuvwxyz'), 'brand')" +
                                         "]")
    for elem in logo_elements:
        size = elem.size
        if size['width'] > 32 and size['height'] > 32:
            img_src = elem.get_attribute('src')
            if img_src:
                img_src = urljoin(driver.current_url, img_src)
                try:
                    img_response = requests.get(img_src, headers=BROWSER_HEADERS, timeout=5)
                    if save_image(img_src, stats, img_response):
                        return True
                except Exception as e:
                    print(f"Error fetching image from URL: {img_src} | {e}")
    return False


def find_logo_in_tag_background(driver, stats, response):
    """Find logo in background images"""
    elements = driver.find_elements(By.CSS_SELECTOR, '*')
    for el in elements:
        try:
            el_id = el.get_attribute('id') or ''
            el_class = el.get_attribute('class') or ''
            if ('logo' in el_id.lower() or 'logo' in el_class.lower() or
                    'brand' in el_id.lower() or 'brand' in el_class.lower()):
                bg_img = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).getPropertyValue('background-image');", el)

                if bg_img and bg_img != 'none':
                    matches = re.findall(r'url\(["\']?(.*?)["\']?\)', bg_img)
                    if matches:
                        img_src = urljoin(driver.current_url, matches[0])
                        try:
                            # Add referer header based on the current page
                            current_headers = BROWSER_HEADERS.copy()
                            current_headers['Referer'] = driver.current_url
                            img_response = requests.get(img_src, headers=current_headers, timeout=5)
                            if save_image(img_src, stats, img_response):
                                return True
                        except Exception as e:
                            print(f"Error fetching background image from URL: {img_src} | {e}")
        except:
            print("find logo in background images failed for " + str(driver.current_url))
    return False


def find_logo_in_tag_children(driver, stats, response):
    """Find logo using Selenium"""
    elements = driver.find_elements(By.XPATH, "//*[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or"
                                              " contains(translate(@class,"
                                              " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'logo')"
                                              " or contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or"
                                              " contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or"
                                              " contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or"
                                              " contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or"
                                              " contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or"
                                              " contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand')]")

    for tag in elements:
        try:
            if tag.tag_name == 'img':
                img_src = tag.get_attribute('src')
                if img_src:
                    img_src = urljoin(driver.current_url, img_src)
                    try:
                        img_response = requests.get(img_src, timeout=5)
                        if save_image(img_src, stats, img_response):
                            return True
                    except Exception as e:
                        print(f"Error fetching image from URL: {img_src} | {e}")
            elif tag.tag_name == 'svg':
                svg_content = tag.get_attribute('outerHTML')
                # Create a response-like object for the SVG content
                from types import SimpleNamespace
                svg_response = SimpleNamespace(
                    status_code=200,
                    text=svg_content,
                    headers={'Content-Type': 'image/svg+xml'},
                    content=svg_content.encode('utf-8')
                )
                if save_image('inline-svg', stats, svg_response):
                    return True
            else:
                try:
                    img = tag.find_element(By.XPATH, ".//img | .//svg")
                    if img.tag_name == 'img':
                        img_src = img.get_attribute('src')
                        if img_src:
                            img_src = urljoin(driver.current_url, img_src)
                            try:
                                # Add referer header based on the current page
                                current_headers = BROWSER_HEADERS.copy()
                                current_headers['Referer'] = driver.current_url
                                img_response = requests.get(img_src, headers=current_headers, timeout=5)
                                if save_image(img_src, stats, img_response):
                                    return True
                            except Exception as e:
                                print(f"Error fetching nested image from URL: {img_src} | {e}")
                    elif img.tag_name == 'svg':
                        svg_content = img.get_attribute('outerHTML')
                        # Create a response-like object for the SVG content
                        from types import SimpleNamespace
                        svg_response = SimpleNamespace(
                            status_code=200,
                            text=svg_content,
                            headers={'Content-Type': 'image/svg+xml'},
                            content=svg_content.encode('utf-8')
                        )
                        if save_image('inline-svg', stats, svg_response):
                            return True
                except Exception:
                    pass
        except Exception as e:
            print(f"Error processing element: {e}")
    return False


def find_logo_in_requests(driver, stats, response):
    """Find logo in network requests"""
    for request in driver.requests:
        if request.response:
            url = request.url.lower()
            if any(url.endswith(ext) for ext in ['.svg', '.png', '.jpg', '.jpeg']) and \
                any(keyword in url for keyword in ['logo', 'brand']):
                try:
                    # Add referer header based on the request URL's domain
                    current_headers = BROWSER_HEADERS.copy()
                    parsed_url = urlparse(url)
                    current_headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                    img_response = requests.get(url, headers=current_headers, timeout=5)
                    if save_image(url, stats, img_response):
                        return True
                except Exception as e:
                    print(f"Error downloading from request URL: {url} | {e}")
    return False

for domain in df['domain']:
    found = False
    stats_build(0, 1, 0, stats)
    for protocol in ['https://', 'http://']:
        url = protocol + domain
        print(f"Încearcă {url}")
        try:
            driver.get(url)
            try:
                # Add proper headers for the main page request
                response = requests.get(url, headers=BROWSER_HEADERS, timeout=5)
            except Exception as e:
                print(f"Eroare la cererea requests pentru {url}: {e}")
                continue

            # Rulăm metodele de căutare a logo-ului
            try:
                if try_selenium_search_all_img_or_svg(driver, stats, response):
                    found = True
                    break
                elif find_logo_in_tag_background(driver, stats, response):
                    found = True
                    break
                elif find_logo_in_tag_children(driver, stats, response):
                    found = True
                    break
                elif find_logo_in_requests(driver, stats, response):
                    found = True
                    break
            except Exception as e:
                print(f"Eroare la procesarea logo-urilor pentru {url}: {e}")
                break
        except TimeoutException:
            print(f"Timeout la încărcarea site-ului: {url}")
        except Exception as e:
            print(f"Eroare la încărcarea site-ului {url}: {e}")

    if not found:
        stats_build(0, 0, 1, stats)