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

# List of domains to exclude (known third-party service providers)
EXCLUDED_DOMAINS = [
    'cookielaw.org',
    'onetrust.com',
    'trustarc.com',
    'googletagmanager.com',
    'google-analytics.com',
    'facebook.net',
    'facebook.com',
    'cloudflare.com',
    'jquery.com',
    'googleapis.com',
    'gstatic.com',
    'recaptcha.net',
    'fontawesome.com',
    'cookiebot.com',
    'consentmanager.net',
    'axeptio.eu',
    'addthis.com',
    'sharethis.com',
    'livechatinc.com',
    'zendesk.com',
    'zopim.com',
    'intercom.io',
    'drift.com',
    'hotjar.com',
    'crisp.chat',
    'tawk.to',
    'cdn-cookieyes.com'
]

# List of strings to exclude in image URLs/paths
EXCLUDED_KEYWORDS = [
    'cookie',
    'consent',
    'gdpr',
    'ccpa',
    'privacy',
    'notification',
    'popup',
    'analytics',
    'tracker',
    'icon',
    'social',
    'facebook',
    'twitter',
    'instagram',
    'linkedin',
    'youtube',
    'pinterest',
    'payment',
    'visa',
    'mastercard',
    'amex',
    'paypal',
    'favicon'
]

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


def is_excluded_url(url):
    """Check if URL should be excluded based on domain or keywords"""
    # Parse the URL to extract the domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()

    # Check if the domain is in the excluded list
    for excluded_domain in EXCLUDED_DOMAINS:
        if excluded_domain in domain:
            print(f"Skipping excluded domain: {domain} in {url}")
            return True

    # Check if the URL contains any excluded keywords
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in path or keyword in domain:
            print(f"Skipping URL with excluded keyword '{keyword}': {url}")
            return True

    return False


def should_keep_image(url, size=None):
    """Determine if image should be kept based on URL and size"""
    if is_excluded_url(url):
        return False

    # If we have size information, check dimensions
    if size and (size['width'] < 40 or size['height'] < 40):
        print(f"Skipping small image ({size['width']}x{size['height']}): {url}")
        return False

    # If the URL looks like a favicon, skip it
    if 'favicon' in url.lower():
        return False

    return True


def save_image(url, stats, response):
    # Check if the URL should be excluded
    if is_excluded_url(url):
        return False

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


def analyze_image_relevance(url, domain, alt_text="", class_name="", parent_id=""):
    """Analyze if image is likely to be a logo based on context"""
    url_lower = url.lower()
    domain_name = domain.split('.')[0].lower()

    score = 0

    # Check if domain name is in the URL
    if domain_name in url_lower:
        score += 3

    # Check for logo indicators in URL
    if 'logo' in url_lower:
        score += 3
    if 'brand' in url_lower:
        score += 2

    # Check alt text and class name for relevance
    if alt_text:
        alt_lower = alt_text.lower()
        if domain_name in alt_lower:
            score += 2
        if 'logo' in alt_lower:
            score += 2

    if class_name:
        class_lower = class_name.lower()
        if 'logo' in class_lower:
            score += 2
        if 'header' in class_lower:
            score += 1
        if 'navbar' in class_lower or 'nav-bar' in class_lower:
            score += 1

    # Higher priority for images in header section
    if parent_id and ('header' in parent_id.lower() or 'navbar' in parent_id.lower()):
        score += 2

    # Deprioritize images that are likely not logos
    for keyword in ['banner', 'footer', 'icon-', 'social', 'payment']:
        if keyword in url_lower:
            score -= 1

    return score


def try_selenium_search_all_img_or_svg(driver, stats, response, domain):
    """Look for logo images with priority given to those in header and with logo in class/id"""
    all_candidates = []
    current_domain = domain

    # First, prioritize header logos
    header_logo_elements = driver.find_elements(By.XPATH,
                                                "//header//img[" +
                                                "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                                " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                                "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                                " 'abcdefghijklmnopqrstuvwxyz'), 'logo')" +
                                                "] | " +
                                                "//nav//img[" +
                                                "contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                                " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or " +
                                                "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                                " 'abcdefghijklmnopqrstuvwxyz'), 'logo')" +
                                                "]")

    # Then, find all potential logo elements
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

    # Combine and prioritize header elements first
    all_elements = list(header_logo_elements) + list(logo_elements)

    for elem in all_elements:
        try:
            size = elem.size
            tag_name = elem.tag_name

            # Skip tiny images
            if size['width'] < 40 or size['height'] < 40:
                continue

            if tag_name == 'img':
                img_src = elem.get_attribute('src')
                if not img_src:
                    continue

                img_src = urljoin(driver.current_url, img_src)
                alt_text = elem.get_attribute('alt') or ""
                class_name = elem.get_attribute('class') or ""

                # Try to get parent element's id for context
                parent_id = ""
                try:
                    parent = driver.execute_script("return arguments[0].parentNode;", elem)
                    parent_id = parent.get_attribute('id') or ""
                except:
                    pass

                # Skip if URL is in excluded list
                if is_excluded_url(img_src):
                    continue

                # Calculate relevance score
                score = analyze_image_relevance(img_src, current_domain, alt_text, class_name, parent_id)

                # Add to candidates
                all_candidates.append({
                    'url': img_src,
                    'score': score,
                    'size': size,
                    'location': 'img_tag'
                })

            elif tag_name == 'svg':
                # Handle SVG elements directly
                svg_content = elem.get_attribute('outerHTML')
                class_name = elem.get_attribute('class') or ""
                elem_id = elem.get_attribute('id') or ""

                # Calculate relevance score for SVG
                score = 0
                if 'logo' in class_name.lower() or 'logo' in elem_id.lower():
                    score += 3
                if 'brand' in class_name.lower() or 'brand' in elem_id.lower():
                    score += 2

                # Try to get parent element's id for context
                parent_id = ""
                try:
                    parent = driver.execute_script("return arguments[0].parentNode;", elem)
                    parent_id = parent.get_attribute('id') or ""
                    if 'header' in parent_id.lower() or 'navbar' in parent_id.lower():
                        score += 2
                except:
                    pass

                all_candidates.append({
                    'svg_content': svg_content,
                    'score': score,
                    'size': size,
                    'location': 'svg_tag'
                })
        except Exception as e:
            print(f"Error processing element: {e}")

    # Sort candidates by score (highest first)
    all_candidates.sort(key=lambda x: x['score'], reverse=True)

    # Try the top candidates
    for candidate in all_candidates:
        try:
            if 'url' in candidate:
                try:
                    # Add referer header based on the current page
                    current_headers = BROWSER_HEADERS.copy()
                    current_headers['Referer'] = driver.current_url
                    img_response = requests.get(candidate['url'], headers=current_headers, timeout=5)

                    print(f"Trying candidate with score {candidate['score']}: {candidate['url']}")
                    if save_image(candidate['url'], stats, img_response):
                        return True
                except Exception as e:
                    print(f"Error fetching image from URL: {candidate['url']} | {e}")
            elif 'svg_content' in candidate:
                # Create a response-like object for the SVG content
                from types import SimpleNamespace
                svg_response = SimpleNamespace(
                    status_code=200,
                    text=candidate['svg_content'],
                    headers={'Content-Type': 'image/svg+xml'},
                    content=candidate['svg_content'].encode('utf-8')
                )

                print(f"Trying SVG candidate with score {candidate['score']}")
                if save_image('inline-svg', stats, svg_response):
                    return True
        except Exception as e:
            print(f"Error processing candidate: {e}")

    return False


def find_logo_in_tag_background(driver, stats, response, domain):
    """Find logo in background images with priority scoring"""
    all_candidates = []
    current_domain = domain

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

                        # Skip if URL is in excluded list
                        if is_excluded_url(img_src):
                            continue

                        # Calculate relevance score
                        score = analyze_image_relevance(img_src, current_domain, "", el_class, el_id)

                        # Get element size
                        size = el.size

                        # Add to candidates
                        all_candidates.append({
                            'url': img_src,
                            'score': score,
                            'size': size,
                            'location': 'background'
                        })
        except:
            continue

    # Sort candidates by score (highest first)
    all_candidates.sort(key=lambda x: x['score'], reverse=True)

    # Try the top candidates
    for candidate in all_candidates:
        try:
            # Add referer header based on the current page
            current_headers = BROWSER_HEADERS.copy()
            current_headers['Referer'] = driver.current_url

            print(f"Trying background candidate with score {candidate['score']}: {candidate['url']}")
            img_response = requests.get(candidate['url'], headers=current_headers, timeout=5)
            if save_image(candidate['url'], stats, img_response):
                return True
        except Exception as e:
            print(f"Error fetching background image from URL: {candidate['url']} | {e}")

    return False


def find_logo_in_tag_children(driver, stats, response, domain):
    """Find logo using Selenium with improved priority scoring"""
    all_candidates = []
    current_domain = domain

    # Find potential logo containers first
    elements = driver.find_elements(By.XPATH, "//*[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'logo') or"
                                              " contains(translate(@class,"
                                              " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'logo')"
                                              " or contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand') or"
                                              " contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                              " 'abcdefghijklmnopqrstuvwxyz'), 'brand')]")

    for tag in elements:
        try:
            tag_id = tag.get_attribute('id') or ''
            tag_class = tag.get_attribute('class') or ''

            if tag.tag_name == 'img':
                img_src = tag.get_attribute('src')
                if img_src:
                    img_src = urljoin(driver.current_url, img_src)

                    # Skip if URL is in excluded list
                    if is_excluded_url(img_src):
                        continue

                    # Get alt text
                    alt_text = tag.get_attribute('alt') or ""

                    # Calculate relevance score
                    score = analyze_image_relevance(img_src, current_domain, alt_text, tag_class, tag_id)

                    # Get size
                    size = tag.size

                    # Add to candidates
                    all_candidates.append({
                        'url': img_src,
                        'score': score,
                        'size': size,
                        'location': 'img_in_logo_container'
                    })
            elif tag.tag_name == 'svg':
                svg_content = tag.get_attribute('outerHTML')

                # Calculate relevance score for SVG
                score = 0
                if 'logo' in tag_id.lower() or 'logo' in tag_class.lower():
                    score += 3
                if 'brand' in tag_id.lower() or 'brand' in tag_class.lower():
                    score += 2

                # Try to get parent context
                parent_id = ""
                try:
                    parent = driver.execute_script("return arguments[0].parentNode;", tag)
                    parent_id = parent.get_attribute('id') or ""
                    if 'header' in parent_id.lower() or 'navbar' in parent_id.lower():
                        score += 2
                except:
                    pass

                # Get size
                size = tag.size

                # Add to candidates
                all_candidates.append({
                    'svg_content': svg_content,
                    'score': score,
                    'size': size,
                    'location': 'svg_in_logo_container'
                })
            else:
                # Try to find images inside this container
                try:
                    imgs = tag.find_elements(By.XPATH, ".//img | .//svg")
                    for img in imgs:
                        if img.tag_name == 'img':
                            img_src = img.get_attribute('src')
                            if img_src:
                                img_src = urljoin(driver.current_url, img_src)

                                # Skip if URL is in excluded list
                                if is_excluded_url(img_src):
                                    continue

                                # Get alt text and class
                                alt_text = img.get_attribute('alt') or ""
                                img_class = img.get_attribute('class') or ""

                                # Calculate relevance score
                                score = analyze_image_relevance(img_src, current_domain, alt_text, img_class, tag_id)
                                # Bonus for being inside a logo/brand container
                                score += 1

                                # Get size
                                size = img.size

                                # Add to candidates
                                all_candidates.append({
                                    'url': img_src,
                                    'score': score,
                                    'size': size,
                                    'location': 'img_in_nested_container'
                                })
                        elif img.tag_name == 'svg':
                            svg_content = img.get_attribute('outerHTML')

                            # Calculate relevance score for SVG
                            score = 0
                            if 'logo' in tag_id.lower() or 'logo' in tag_class.lower():
                                score += 3
                            if 'brand' in tag_id.lower() or 'brand' in tag_class.lower():
                                score += 2
                            # Bonus for being inside a logo/brand container
                            score += 1

                            # Get size
                            size = img.size

                            # Add to candidates
                            all_candidates.append({
                                'svg_content': svg_content,
                                'score': score,
                                'size': size,
                                'location': 'svg_in_nested_container'
                            })
                except Exception:
                    pass
        except Exception as e:
            print(f"Error processing element: {e}")

    # Sort candidates by score (highest first)
    all_candidates.sort(key=lambda x: x['score'], reverse=True)

    # Try the top candidates
    for candidate in all_candidates:
        try:
            if 'url' in candidate:
                try:
                    # Add referer header based on the current page
                    current_headers = BROWSER_HEADERS.copy()
                    current_headers['Referer'] = driver.current_url

                    print(f"Trying child candidate with score {candidate['score']}: {candidate['url']}")
                    img_response = requests.get(candidate['url'], headers=current_headers, timeout=5)
                    if save_image(candidate['url'], stats, img_response):
                        return True
                except Exception as e:
                    print(f"Error fetching nested image from URL: {candidate['url']} | {e}")
            elif 'svg_content' in candidate:
                # Create a response-like object for the SVG content
                from types import SimpleNamespace
                svg_response = SimpleNamespace(
                    status_code=200,
                    text=candidate['svg_content'],
                    headers={'Content-Type': 'image/svg+xml'},
                    content=candidate['svg_content'].encode('utf-8')
                )

                print(f"Trying SVG child candidate with score {candidate['score']}")
                if save_image('inline-svg', stats, svg_response):
                    return True
        except Exception as e:
            print(f"Error processing candidate: {e}")

    return False


def find_logo_in_requests(driver, stats, response, domain):
    """Find logo in network requests with better filtering"""
    all_candidates = []
    current_domain = domain

    for request in driver.requests:
        if request.response:
            url = request.url.lower()

            # Skip if URL is in excluded list
            if is_excluded_url(url):
                continue

            # Check if it looks like a logo image
            if any(url.endswith(ext) for ext in ['.svg', '.png', '.jpg', '.jpeg']) and \
                    any(keyword in url for keyword in ['logo', 'brand']):
                # Calculate relevance score
                score = analyze_image_relevance(url, current_domain)

                # Add to candidates
                all_candidates.append({
                    'url': url,
                    'score': score,
                    'location': 'network_request'
                })

    # Sort candidates by score (highest first)
    all_candidates.sort(key=lambda x: x['score'], reverse=True)

    # Try the top candidates
    for candidate in all_candidates:
        try:
            # Add referer header based on the request URL's domain
            current_headers = BROWSER_HEADERS.copy()
            parsed_url = urlparse(candidate['url'])
            current_headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            print(f"Trying network request candidate with score {candidate['score']}: {candidate['url']}")
            img_response = requests.get(candidate['url'], headers=current_headers, timeout=5)
            if save_image(candidate['url'], stats, img_response):
                return True
        except Exception as e:
            print(f"Error downloading from request URL: {candidate['url']} | {e}")

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
                if try_selenium_search_all_img_or_svg(driver, stats, response, domain):
                    found = True
                    break
                elif find_logo_in_tag_background(driver, stats, response, domain):
                    found = True
                    break
                elif find_logo_in_tag_children(driver, stats, response, domain):
                    found = True
                    break
                elif find_logo_in_requests(driver, stats, response, domain):
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

# Close the driver when done
driver.quit()