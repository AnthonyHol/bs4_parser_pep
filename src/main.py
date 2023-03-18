import logging
import re
from typing import List, Tuple
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    A_TAG,
    ABBR_TAG,
    BASE_DIR,
    CLASS,
    DIV_TAG,
    DL_TAG,
    DOWNLOAD_CLASS,
    DOWNLOAD_ROLE,
    EXPECTED_STATUS,
    H1_TAG,
    HREF_TAG,
    ID,
    LATEST_VER_CLASS,
    MAIN_DOC_URL,
    PEP_CLASS,
    PEP_ID,
    PEP_URL,
    SECTION_TAG,
    TABLE_TAG,
    TOCTREE_CLASS,
    UL_TAG,
    WHATSNEW_ID,
)
from exceptions import TagNotFoundException
from outputs import control_output
from utils import find_tag, get_response, get_soup


def whats_new(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    """Функция парсинга раздела 'Whats new'."""

    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")

    soup = get_soup(session, whats_new_url)

    main_div = find_tag(soup, SECTION_TAG, attrs={ID: WHATSNEW_ID})

    div_with_ul = find_tag(main_div, DIV_TAG, attrs={CLASS: TOCTREE_CLASS})

    sections_by_python = div_with_ul.find_all(
        "li", attrs={CLASS: "toctree-l1"}
    )

    results = [("Ссылка на статью", "Заголовок", "Редактор, Автор")]

    for section in tqdm(sections_by_python):
        version_a_tag = section.find(A_TAG)
        href = version_a_tag[HREF_TAG]
        version_link = urljoin(whats_new_url, href)

        soup = get_soup(session, version_link)

        h1 = find_tag(soup, H1_TAG)
        dl = find_tag(soup, DL_TAG)

        dl_text = dl.text.replace("\n", " ")

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    """Функция парсинга информации о версиях Python."""

    soup = get_soup(session, MAIN_DOC_URL)

    sidebar = find_tag(soup, DIV_TAG, {CLASS: LATEST_VER_CLASS})
    ul_tags = sidebar.find_all(UL_TAG)

    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all(A_TAG)
            break
        else:
            raise TagNotFoundException

    results = [("Ссылка на документацию", "Версия", "Статус")]

    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"

    for a_tag in a_tags:
        link = a_tag[HREF_TAG]
        text_match = re.search(pattern, a_tag.text)
        version, status = text_match.groups() if text_match else a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session: requests_cache.CachedSession) -> None:
    """Функция парсинга документации Python с сохранением в файл."""
    download_url = urljoin(MAIN_DOC_URL, "download.html")

    response = get_response(session, download_url)

    soup = get_soup(session, download_url)

    main_tag = soup.find(DIV_TAG, {"role": DOWNLOAD_ROLE})
    table_tag = main_tag.find(TABLE_TAG, {CLASS: DOWNLOAD_CLASS})

    pdf_a4_tag = table_tag.find(
        A_TAG, {HREF_TAG: re.compile(r".+pdf-a4\.zip$")}
    )

    pdf_a4_link = pdf_a4_tag[HREF_TAG]

    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_link)

    filename = archive_url.split("/")[-1]
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    with open(archive_path, "wb") as file:
        file.write(response.content)

    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    """Функция парсинга раздела PEP,
    подсчет количество различных статусов PEP."""

    soup = get_soup(session, PEP_URL)

    pep_table = find_tag(soup, SECTION_TAG, attrs={ID: PEP_ID})
    pep_table_data = find_tag(pep_table, "tbody")
    pep_tags = pep_table_data.find_all("tr")

    errors = []
    pep_list = []
    statuses = []
    result = [("Статус", "Количество")]

    for pep_tag in tqdm(pep_tags):
        preview_status = find_tag(pep_tag, ABBR_TAG).text[1:]
        href = find_tag(pep_tag, A_TAG)[HREF_TAG]
        pep_link = urljoin(PEP_URL, href)

        response = get_response(session, pep_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features="lxml")

        description = find_tag(soup, DL_TAG, attrs={CLASS: PEP_CLASS})

        td = description.find(string="Status")
        status = td.find_parent().find_next_sibling().text
        pep_list.append(status)

        try:
            if status not in EXPECTED_STATUS[preview_status]:
                errors.append((pep_link, preview_status, status))
        except KeyError:
            logging.error("Unexpected Status: " f"{preview_status}")

    for status_list in EXPECTED_STATUS.values():
        for status in status_list:
            if status not in statuses:
                statuses.append(status)
                result.append((status, pep_list.count(status)))

    result.append(("Total", len(pep_list)))

    return result


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main() -> None:
    """Главная функция."""
    configure_logging()
    logging.info("Парсер запущен!")

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    logging.info(f"Аргументы командной строки: {args}")

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()
