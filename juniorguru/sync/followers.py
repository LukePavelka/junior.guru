import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import click
import requests
from lxml import html
from playwright.sync_api import TimeoutError, sync_playwright

from juniorguru.cli.sync import default_from_env, main as cli
from juniorguru.lib import loggers
from juniorguru.lib.text import extract_text
from juniorguru.models.base import db
from juniorguru.models.followers import Followers


logger = loggers.from_path(__file__)


YOUTUBE_URL = "https://www.youtube.com/@juniordotguru"

YOUTUBE_CONSENT_FORM_URL = "https://consent.youtube.com/save"

YOUTUBE_LANGUAGE_FORM_URL = "https://consent.youtube.com/ml"

LINKEDIN_URL = "https://www.linkedin.com/company/juniorguru"

LINKEDIN_PERSONAL_URL = "https://www.linkedin.com/posts/honzajavorek_courting-haskell-honza-javorek-activity-6625070791035756544-J3Hr"


@cli.sync_command()
@click.option(
    "--history-path",
    default="juniorguru/data/followers.jsonl",
    type=click.Path(path_type=Path),
)
@click.option("--ecomail-api-key", default=default_from_env("ECOMAIL_API_KEY"))
@click.option("--ecomail-list", "ecomail_list_id", default=1, type=int)
@db.connection_context()
def main(history_path: Path, ecomail_api_key: str, ecomail_list_id: int):
    logger.info("Preparing database")
    Followers.drop_table()
    Followers.create_table()

    logger.info("Reading history from a file")
    history_path.touch(exist_ok=True)
    with history_path.open() as f:
        for line in f:
            Followers.deserialize(line)

    month = f"{date.today():%Y-%m}"
    logger.info(f"Current month: {month}")

    logger.info("Getting newsletter subscribers from Ecomail")
    response = requests.get(
        f"https://api2.ecomailapp.cz/lists/{ecomail_list_id}/subscribers",
        headers={
            "key": ecomail_api_key,
            "User-Agent": "JuniorGuruBot (+https://junior.guru)",
        },
    )
    response.raise_for_status()
    subscribers_count = response.json()["total"]
    Followers.add(month=month, name="newsletter", count=subscribers_count)

    scrapers = {
        "youtube": scrape_youtube,
        "linkedin": scrape_linkedin,
        # "linkedin_personal": scrape_linkedin_personal,   # they removed the follower count
        "mastodon": scrape_mastodon,
    }
    for name, scrape in scrapers.items():
        logger.info(f"Scraping {name!r}")
        if count := scrape():
            logger.info(f"Saving result: {count}")
            Followers.add(month=month, name=name, count=count)
        else:
            logger.warning(f"Result: {count}")

    logger.info("Saving history to a file")
    with history_path.open("w") as f:
        for db_object in Followers.history():
            f.write(db_object.serialize())


def scrape_youtube():
    logger.info("Scraping YouTube")
    session = requests.Session()
    response = session.get(YOUTUBE_URL)
    response.raise_for_status()
    html_tree = html.fromstring(response.content)
    try:
        consent_form = [
            form for form in html_tree.forms if form.action == YOUTUBE_CONSENT_FORM_URL
        ][0]
        response = session.request(
            consent_form.method.lower(),
            consent_form.action,
            params=consent_form.form_values(),
        )
        response.raise_for_status()
    except IndexError:
        logger.warning("There is no YouTube consent form")
    match = re.search(r'"(\d+) (odběratelů|subscribers)"', response.text)
    try:
        return int(match.group(1))
    except AttributeError:
        logger.error(f"Scraping failed!\n\n{response.text}")
        return None


def scrape_linkedin():
    logger.info("Scraping LinkedIn")
    text = None

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch()
        page = browser.new_page()

        # try LinkedIn first
        try:
            page.goto(LINKEDIN_URL, wait_until="networkidle")
            if "/authwall" in page.url:
                logger.error(f"Loaded {page.url}")
            else:
                text = str(page.content())
        except TimeoutError:
            logger.error(f"Time out on {LINKEDIN_URL}")

        # if we've got authwall or timeout, try Google results
        if text is None:
            google_query = f"{LINKEDIN_URL} sledujících"
            google_url = (
                f"https://www.google.cz/search?{urlencode(dict(q=google_query))}"
            )
            page.goto(google_url, wait_until="networkidle")
            html_tree = html.fromstring(page.content())
            html_link = html_tree.cssselect(f'a[href^="{LINKEDIN_URL}"]')[0]
            html_item = html_link.xpath("./ancestor::*[@data-hveid][position() = 1]")[0]
            text = extract_text(html.tostring(html_item))

    match = re.search(
        r"Junior Guru \| (\d+) (followers on|sledujících uživatelů na) LinkedIn.", text
    )
    try:
        return int(match.group(1))
    except (AttributeError, ValueError):
        logger.error(f"Scraping failed!\n\n{text}")
        return None


def scrape_linkedin_personal():
    logger.info("Scraping personal LinkedIn")
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch()
        page = browser.new_page()
        page.goto(LINKEDIN_PERSONAL_URL, wait_until="networkidle")
        if "/authwall" in page.url:
            logger.error(f"Loaded {page.url}")
            return None
        response_text = str(page.content())
        browser.close()
    html_tree = html.fromstring(response_text)
    followers_element = html_tree.cssselect(
        '[class*="public-post-author-card__followers"]'
    )[0]
    match = re.search(
        r"([\d,]+)\s*(followers|sledujících)", followers_element.text_content()
    )
    try:
        return int(match.group(1).replace(",", ""))
    except (AttributeError, ValueError):
        logger.error(f"Scraping failed!\n\n{response_text}")
        return None


def scrape_mastodon():
    logger.info("Scraping Mastodon")
    urls = [
        "https://mastodonczech.cz/@honzajavorek",
        "https://mastodon.social/@honzajavorek@mastodonczech.cz"
        "https://witter.cz/@honzajavorek@mastodonczech.cz",
    ]
    for url in urls:
        try:
            response = requests.get(
                url, headers={"User-Agent": "JuniorGuruBot (+https://junior.guru)"}
            )
            response.raise_for_status()
            html_tree = html.fromstring(response.content)
            description = html_tree.cssselect('meta[name="description"]')[0].get(
                "content"
            )
            match = re.search(
                r"(\d+)\s+(followers|sledujících)", description, re.IGNORECASE
            )
            return int(match.group(1))
        except Exception as e:
            details = f"\n\n{e.response.text}" if getattr(e, "response", None) else ""
            logger.exception(f"Scraping failed!{details}")
    return None
