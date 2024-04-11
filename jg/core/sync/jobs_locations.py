from jg.core.cli.sync import main as cli
from jg.core.lib import loggers
from jg.core.lib.locations import fetch_locations
from jg.core.models.base import db
from jg.core.models.job import ListedJob


logger = loggers.from_path(__file__)


@cli.sync_command(dependencies=["jobs-listing"])
@db.connection_context()
def main():
    for job in ListedJob.listing():
        if job.locations_raw:
            logger.debug(f"Normalizing locations for {job!r}: {job.locations_raw!r}")
            job.locations = fetch_locations(
                job.locations_raw,
                debug_info=dict(title=job.title, company_name=job.company_name),
            )
            logger.info(
                f"Locations for {job!r} normalized: {job.locations_raw} → {job.locations}"
            )
            job.save()
        else:
            logger.debug(f"Job {job!r} has no locations set")
