from bs4 import BeautifulSoup
import re
import requests

from . import config
import logging
logger = logging.getLogger(__name__)


ELEMENTS = ["li", "footer", "header", "nav", "aside", "figure", "blockquote", "img"]

WORDS = ["image", "img", "footer", "pie", "banner", "autoria",
         "cookie", "themes", "foto", "media", "encabezado", "registro",
         "entradilla", "telefono", "comment", "hidden", "dialog", "fail",
         "fecha", "tweet", "twitter", "comentario", "date", "ColumnaDerecha"]

STYLES = ["text-align: center", "display: none"]

URL_REGEX = re.compile(r'(?P<protocol>https?:\/\/(www.)?(?P<domain>[^\s\/]+)(\/\S+)?\b)')
HASHTAG_REGEX = re.compile(r'#(\S+)\b')
TWITTER_USER_REGEX = re.compile(r'@(\S+)\b')

URL_STRING = '<a href="{}" target="_blank">{}</a>'


def delete_attrs(soup, words):
    for word in words:
        for t in soup.find_all(attrs=re.compile(word, re.IGNORECASE)):
            t.extract()
        for t in soup.find_all(attrs={'id': re.compile(word, re.IGNORECASE)}):
            t.extract()


def delete_elements(soup, elements):
    for element in elements:
        for t in soup.find_all(element):
            t.extract()


def delete_styles(soup, styles):
    for style in styles:
        style = style.replace(" ", "\s*")
        for t in soup.find_all(style=re.compile(style, re.IGNORECASE)):
            t.extract()


def fetch_url(url):
    text = None
    logger.debug("Requesting html from ulr " + url)
    try:
        response = requests.get(url, proxies=config.private.PROXY, verify=False)
        response.raise_for_status()
    except requests.HTTPError:
        logger.error("Clean html request failed with status code {}".format(response.status_code))
        logger.error("for url: " + url)
    except requests.RequestException:
        logger.exception("Clean html request failed")
    else:
        text = response.text

    return text or ""


def filter_html(html):
    text = ""

    soup = BeautifulSoup(html, "html.parser")

    delete_elements(soup, ELEMENTS)
    delete_attrs(soup, WORDS)
    delete_styles(soup, STYLES)
    paragraphs = soup.find_all('p')

    matches = []
    for p in paragraphs:
        if not any(p in m.descendants for m in paragraphs):
            matches.append(p)

    for m in matches:
        if len(m.text) > 100:
            text += m.text + " "

    return text


def remove_html_tags(html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', html)

    cleantext.replace("\n", " ")
    cleantext.replace("\t", " ")
    return re.sub(r'\s+', ' ', cleantext)


def parse_link(url):
    """Gives the parsed content a quoted style."""
    text = filter_html(fetch_url(url))
    return '<p class="alert alert-info">{}</p>'.format(text) if text else ""


def get_urls(text):
    return [match[0] for match in URL_REGEX.findall(text)]


def remove_urls(text):
    return URL_REGEX.sub('', text)


def linkify_urls(text):
    return URL_REGEX.sub(URL_STRING.format('\g<0>', '\g<0>'), text)


def get_hashtags(text):
    return HASHTAG_REGEX.findall(text)


def linkify_hashtags(text, source):
    if source == 'facebook':
        link = 'https://www.facebook.com/hashtag/'
    if source == 'twitter':
        link = 'https://twitter.com/hashtag/'
    return HASHTAG_REGEX.sub(URL_STRING.format(link + '\g<1>', '\g<0>'), text)


def linkify_twitter_users(text):
    return TWITTER_USER_REGEX.sub(URL_STRING.format('https://twitter.com/' + '\g<1>', '\g<0>'), text)


def get_domain(url):
    return URL_REGEX.match(url).groupdict('domain')
