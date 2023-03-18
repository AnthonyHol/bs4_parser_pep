import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


def get_response(session, url):
    """Функция получения ответа."""
    try:
        response = session.get(url)
        response.encoding = "utf-8"
        return response
    except RequestException:
        logging.exception(
            f"Возникла ошибка при загрузке страницы {url}", stack_info=True
        )


def get_soup(session, url) -> BeautifulSoup:
    """Функция получения SOUP."""
    response = get_response(session, url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features="lxml")

    return soup


def find_tag(soup, tag, attrs=None):
    """Функция поиска тега в SOUP."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f"Не найден тег {tag} {attrs}"
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
