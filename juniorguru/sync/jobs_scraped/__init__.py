from datetime import date
from pathlib import Path

import click
from peewee import OperationalError

from juniorguru.cli.sync import main as cli
from juniorguru.lib import loggers
from juniorguru.models.base import db
from juniorguru.models.job import ScrapedJob
from juniorguru.sync.jobs_scraped.processing import (
    filter_relevant_paths,
    postprocess_jobs,
    process_paths,
)


PREPROCESS_PIPELINES = [
    "juniorguru.sync.jobs_scraped.pipelines.blocklist",
    "juniorguru.sync.jobs_scraped.pipelines.boards_ids",
]

POSTPROCESS_PIPELINES = [
    "juniorguru.sync.jobs_scraped.pipelines.description_parser",
    "juniorguru.sync.jobs_scraped.pipelines.features_parser",
    "juniorguru.sync.jobs_scraped.pipelines.gender_remover",
    "juniorguru.sync.jobs_scraped.pipelines.emoji_remover",
    "juniorguru.sync.jobs_scraped.pipelines.company_url_cleaner",
    "juniorguru.sync.jobs_scraped.pipelines.employment_types_cleaner",
    "juniorguru.sync.jobs_scraped.pipelines.juniority_re_score",
]


logger = loggers.from_path(__file__)


@cli.sync_command(dependencies=["scrape-jobs"])
@click.option("--reuse-db/--no-reuse-db", default=False)
@click.option("--latest-seen-on", default=None, type=date.fromisoformat)
def main(reuse_db, latest_seen_on):
    raise NotImplementedError()
    # paths = list(Path(FEEDS_DIR).glob("**/*.jsonl.gz"))
    # logger.info(f"Found {len(paths)} .json.gz paths")

    # with db.connection_context():
    #     if reuse_db:
    #         logger.warning("Reusing of existing jobs database is enabled!")
    #         try:
    #             latest_seen_on = ScrapedJob.latest_seen_on()
    #             logger.info(f"Last jobs seen on: {latest_seen_on}")
    #         except OperationalError:
    #             logger.warning("Jobs database not operational!")

    #     if latest_seen_on:
    #         paths = filter_relevant_paths(paths, latest_seen_on)
    #         logger.info(f"Keeping {len(paths)} relevant .json.gz paths")
    #     else:
    #         logger.info("Not reusing jobs database")
    #         ScrapedJob.drop_table()
    #         ScrapedJob.create_table()

    # process_paths(paths, PREPROCESS_PIPELINES)
    # postprocess_jobs(POSTPROCESS_PIPELINES)
