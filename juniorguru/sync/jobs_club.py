import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from discord import Embed, File, ui

from juniorguru.cli.sync import main as cli
from juniorguru.lib import discord_sync, loggers
from juniorguru.lib.asyncio_extra import chunks
from juniorguru.lib.discord_club import (ClubChannel, mutating,
                                         fetch_threads, is_thread_after)
from juniorguru.models.base import db
from juniorguru.models.job import ListedJob


JOBS_POSTING_CHUNK_SIZE = 2

JOBS_REPEATING_PERIOD_DAYS = 30

PACKAGE_DIR = Path('juniorguru')


logger = loggers.from_path(__file__)


@cli.sync_command(dependencies=['club-content', 'jobs-locations', 'jobs-logos'])
def main():
    discord_sync.run(discord_task)


@db.connection_context()
async def discord_task(client):
    since_at = datetime.now(timezone.utc) - timedelta(days=JOBS_REPEATING_PERIOD_DAYS)
    logger.info(f'Figuring out which jobs are not yet in the channel since {since_at}')
    channel = await client.club_guild.fetch_channel(ClubChannel.JOBS)
    urls = [get_effective_url(message) async for message
            in fetch_starting_messages(channel, after=since_at)]
    urls = frozenset(filter(None, urls))
    logger.info(f'Found {len(urls)} jobs since {since_at}')
    jobs = [job for job in ListedJob.listing() if job.effective_url not in urls]
    logger.info(f'Posting {len(jobs)} new jobs to the channel')
    jobs_chunks = chunks(jobs, size=JOBS_POSTING_CHUNK_SIZE)
    for n, jobs_chunk in enumerate(jobs_chunks, start=1):
        logger.debug(f'Processing chunk #{n} of {len(jobs_chunk)} jobs')
        await asyncio.gather(*[post_job(channel, job) for job in jobs_chunk])


async def fetch_starting_messages(channel, after=None):
    async for thread in fetch_threads(channel):
        if is_thread_after(thread, after=after):
            yield await thread.fetch_message(thread.id)


def get_effective_url(message):
    try:
        action_row = message.components[0]
        button = action_row.children[0]
        return button.url
    except IndexError:
        return None


async def post_job(channel, job):
    logger[str(job.id)].info(f'Posting {job!r}: {job.effective_url}')
    # https://github.com/Pycord-Development/pycord/issues/1949
    embed = Embed(title=job.company_name)
    with mutating(channel) as channel:
        thread = await channel.create_thread(job.title,
                                             job.location,
                                             embed=embed,
                                             view=ui.View(ui.Button(emoji='👉',
                                                                    label='Zjistit víc',
                                                                    url=job.effective_url)))
    if job.company_logo_path:
        embed.set_thumbnail(url=f"attachment://{Path(job.company_logo_path).name}")
        message = await thread.fetch_message(thread.id)
        with mutating(message) as message:
            await message.edit(file=File(PACKAGE_DIR / job.company_logo_path),
                               embed=embed)
