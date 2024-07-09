from datetime import date
from pathlib import Path

import click
import yaml

from jg.coop.lib import loggers
from jg.coop.models.base import db
from jg.coop.sync.organizations import SPONSORS_YAML_PATH, SponsorsConfig, get_renews_on


logger = loggers.from_path(__file__)


@click.command()
@click.option(
    "--path",
    default=SPONSORS_YAML_PATH,
    type=click.Path(path_type=Path),
)
@click.option(
    "--today",
    default=lambda: date.today().isoformat(),
    type=date.fromisoformat,
)
@click.option("--weekday", default=1, type=int)
@click.option("--days", default=60, type=int)
@db.connection_context()
def main(path: Path, today: date, weekday: int, days: int):
    if today.isoweekday() != weekday:
        logger.warning(f"No check today (weekday {today.isoweekday()} ≠ {weekday})")
        return

    logger.info(f"Loading sponsors data from {path}")
    sponsors_yaml_data = yaml.safe_load(path.read_text())
    sponsors = SponsorsConfig(**sponsors_yaml_data)

    renewals = []
    for sponsor in sponsors.registry:
        if renews_on := get_renews_on(sponsor.periods, today):
            logger.info(f"{sponsor.name} renews on {renews_on}")

            remains_days = (renews_on - today).days
            if remains_days <= days:
                logger.error(f"{sponsor.name} renews soon! ({remains_days} days)")
                renewals.append(sponsor)
        else:
            logger.debug(f"{sponsor.name} does not renew")

    if renewals:
        raise click.Abort()
