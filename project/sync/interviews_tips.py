from datetime import timedelta

from discord import Color, Embed

from project.cli.sync import main as cli
from project.lib import discord_task, loggers
from project.lib.discord_club import (
    ClubChannelID,
    ClubClient,
    is_message_over_period_ago,
)
from project.lib.mutations import mutating_discord
from project.models.base import db
from project.models.club import ClubMessage
from project.models.mentor import Mentor


INTERVIEWS_EMOJI = "💁"


logger = loggers.from_path(__file__)


@cli.sync_command(dependencies=["club-content", "mentoring"])
def main():
    discord_task.run(sync_interviews_tips)


@db.connection_context()
async def sync_interviews_tips(client: ClubClient):
    last_message = ClubMessage.last_bot_message(
        ClubChannelID.INTERVIEWS, INTERVIEWS_EMOJI
    )
    if is_message_over_period_ago(last_message, timedelta(days=30)):
        logger.info("Last reminder is more than one month old!")
        channel = await client.fetch_channel(ClubChannelID.INTERVIEWS)
        embed_mentors_description = "\n".join(
            [
                f"[{mentor.user.display_name}]({mentor.message_url}) – {mentor.topics}"
                for mentor in Mentor.interviews_listing()
            ]
        )
        embed_mentors = Embed(
            color=Color.orange(), description=embed_mentors_description
        )
        embed_handbook = Embed(
            description=(
                "📖 Než se pustíš do pohovorů, přečti si "
                "[příručku na junior.guru](https://junior.guru/handbook/interview/) o tom, "
                "jak se na ně připravit."
            )
        )

        logger.info("Sending new reminder")
        with mutating_discord(channel) as proxy:
            await proxy.send(
                content=(
                    f"{INTERVIEWS_EMOJI} Pomohla by ti soustavnější příprava na přijímací řízení? "
                    "Chceš si jednorázově vyzkoušet pohovor nanečisto, česky nebo anglicky? "
                    f"Někteří členové se v <#{ClubChannelID.MENTORING}> k takovým konzultacím nabídli!"
                ),
                embeds=[embed_mentors, embed_handbook],
            )

        if last_message:
            logger.info("Deleting previous reminder")
            message = await channel.fetch_message(last_message.id)
            with mutating_discord(message) as proxy:
                await proxy.delete()
