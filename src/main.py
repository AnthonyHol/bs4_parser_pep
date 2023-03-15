import logging
import re
from typing import List, Tuple
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")

    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features="lxml")

    main_div = find_tag(soup, "section", attrs={"id": "what-s-new-in-python"})

    div_with_ul = find_tag(main_div, "div", attrs={"class": "toctree-wrapper"})

    sections_by_python = div_with_ul.find_all("li", attrs={"class": "toctree-l1"})

    results = [("Ссылка на статью", "Заголовок", "Редактор, Автор")]

    for section in tqdm(sections_by_python):
        version_a_tag = section.find("a")
        href = version_a_tag["href"]
        version_link = urljoin(whats_new_url, href)
        response = session.get(version_link)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        h1 = find_tag(soup, "h1")
        dl = find_tag(soup, "dl")

        dl_text = dl.text.replace("\n", " ")

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, "lxml")

    sidebar = find_tag(soup, "div", {"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all("ul")

    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
        else:
            raise Exception("Ничего не нашлось")

    results = [("Ссылка на документацию", "Версия", "Статус")]

    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"

    for a_tag in a_tags:
        link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session: requests_cache.CachedSession) -> None:
    response = get_response(session, urljoin(MAIN_DOC_URL, "download.html"))
    if response is None:
        return

    soup = BeautifulSoup(response.text, "lxml")

    main_tag = soup.find("div", {"role": "main"})
    table_tag = main_tag.find("table", {"class": "docutils"})

    pdf_a4_tag = table_tag.find("a", {"href": re.compile(r".+pdf-a4\.zip$")})

    pdf_a4_link = pdf_a4_tag["href"]

    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_link)

    filename = archive_url.split("/")[-1]
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    with open(archive_path, "wb") as file:
        file.write(response.content)

    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session: requests_cache.CachedSession) -> List[Tuple[str]]:
    response = get_response(session, PEP_URL)
    if response is None:
        return None

    soup = BeautifulSoup(response.text, features="lxml")
    pep_table = find_tag(soup, "section", attrs={"id": "numerical-index"})
    pep_table_data = find_tag(pep_table, "tbody")
    pep_tags = pep_table_data.find_all("tr")

    errors = []
    pep_list = []
    statuses = []
    result = [("Статус", "Количество")]

    for pep_tag in tqdm(pep_tags):
        preview_status = find_tag(pep_tag, "abbr").text[1:]
        href = find_tag(pep_tag, "a")["href"]
        pep_link = urljoin(PEP_URL, href)

        response = get_response(session, pep_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features="lxml")
        description = find_tag(soup, "dl", attrs={"class": "rfc2822 field-list simple"})

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
