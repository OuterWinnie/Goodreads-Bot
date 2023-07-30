
import logging
from types import NoneType
from typing import List
from rich.logging import RichHandler
from rich import print
from rich.pretty import pprint
from rich.traceback import install
from bs4 import BeautifulSoup, NavigableString
import re
import requests
from urllib.parse import urlparse, urljoin

from configuration import LOGLEVEL
from rss_helper import Review

if logging.root.level == logging.DEBUG:
    install(show_locals=True)
else:
    install(show_locals=False)

FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")

rss_url = "https://bookwyrm.social/user/potajito/rss-reviews"
user_profile_url = "https://bookwyrm.social/user/christa/"

def parse_book_name (s: str) -> str:
    """Extracts book name from a string, searching for the text between double quotes ("text")

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    
    # Find the index of the first double quote
    start_index = s.find('"')
    # Find the index of the second double quote after the first one
    end_index = s.find('"', start_index + 1)

    # Extract the substring between the two double quotes
    result = s[start_index + 1:end_index]
    return result
    

def parse_score (s: str) -> int:
    """Extracts score from a string , searching for the number between parenthesis "(4 stars)"

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    pattern = r"(\d+ stars)"
    match = re.search(pattern, s)
    
    if match:
        stars_string = match.group(1) # Extract the string "x stars". We do it like this to avoid extracting the wrong info with books that could contain numbers in the title
        # Now we extract the score
        score = int(stars_string.split()[0])
        return score
    else:
        log.debug(f"No score found on {s}")
        return 0

# Find all 'a' tags with 'href' containing '/book/' and have "rated" under the <h3> tag with class "has-text-weight-bold"
def find_book_title(entry: NavigableString) -> str:
    try:
        tag: NavigableString = entry.find('a', href=lambda href: href and '/book/' in href)
        if tag:
            return tag.get_text().strip()
    except Exception:
        return 'Unknown book'
    
def find_book_author(entry: NavigableString) -> str:
    try:
        tag: NavigableString = entry.find('a', href=lambda href: href and '/author/' in href)
        if tag:
            book_author = tag.get_text().strip()
            if book_author:
                return book_author
        else:
            return 'Unknown author'        
    except Exception:
        return 'Unknown author'
    
def parse_user_profile (profile_url: str) -> dict:
    reviews: List[Review] = []
    try:
        profile_url_domain = urlparse(profile_url).hostname
        profile_url_scheme = urlparse(profile_url).scheme
        reviews_url = requests.get(urljoin(user_profile_url,'reviews-comments'))
        soup = BeautifulSoup(reviews_url.text,"html.parser")
        
        user_image_url = soup.find('img', class_=re.compile(r'avatar image*')).get('src')
         
        header_entries: List[NavigableString] = soup.find_all('h3', class_='has-text-weight-bold')
        #box_entries = soup.find_all('section', class_='card-content')

        for entry in header_entries:
            if ' rated ' in entry.text:
                username = entry.find('span', itemprop='name').text.strip()
                book_name = find_book_title(entry)
                score_in_stars = entry.select_one('.stars .is-sr-only').text.strip()
                score = int(re.findall(r'\d+', score_in_stars)[0])

                section_tag = entry.find_next('section', class_='card-content')
                author = find_book_author(entry)
                section_a_tags = section_tag.find_all('a')
                section_img_tag = section_tag.find("img", class_="book-cover")
                try:
                    image_url = section_img_tag.get('src')
                except Exception:
                    image_url = 'https://cover2coverbookdesign.com/site/wp-content/uploads/2019/03/geometric1.jpg'
                
                for a_tag in section_a_tags:
                    if "/book/" in a_tag.get('href'):
                        book_url = f"{profile_url_scheme}://{profile_url_domain}{a_tag.get('href')}" 
                        
                        # log.debug(book_url)
                        break
                
                clean_string = f"{username} rated {book_name} by {author}: {score}"
                # log.info(clean_string)
            if ' reviewed ' in entry.text:
                username = entry.find('span', itemprop='name').text.strip()
                # book_name = entry.find(find_book_title).text.split()
                book_name = find_book_title(entry)
                author = find_book_author(entry)

                section_tag = entry.find_next('section', class_='card-content')
                score_in_stars = section_tag.find('span', class_='is-sr-only').text.strip()
                score = int(re.findall(r'\d+', score_in_stars)[0])
                
                section_a_tags = section_tag.find_all('a')
                section_img_tag = section_tag.find("img", class_="book-cover")
                try:
                    image_url = section_img_tag.get('src')
                except Exception:
                    image_url = 'https://cover2coverbookdesign.com/site/wp-content/uploads/2019/03/geometric1.jpg'
                
                for a_tag in section_a_tags:
                    if "/book/" in a_tag.get('href'):
                        book_url = f"{profile_url_scheme}://{profile_url_domain}{a_tag.get('href')}" 
                        
                        # log.debug(book_url)
                        break
                current_review = {
                "title": book_name,
                "score": score,
                "author": author,
                "url": book_url,
                "image_url": image_url,
                "user_url": profile_url,
                "username": username,
                "user_image_url": user_image_url
                }
                pprint(current_review)
                reviews.append(current_review)
        # pprint(reviews)
        return reviews
    
                        
    except Exception as error:
        print('Could not parse the xml: ', profile_url)
        print(error)

parse_user_profile(user_profile_url)
# parse_rss(rss_url)
    