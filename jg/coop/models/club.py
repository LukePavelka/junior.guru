import datetime
import math
from datetime import date, timedelta
from enum import StrEnum, auto, unique
from itertools import groupby
from operator import attrgetter
from typing import Iterable, Optional, Self, TypeVar

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
    fn,
)

from jg.coop.lib.discord_club import ClubChannelID, ClubMemberID, parse_message_url
from jg.coop.models.base import BaseModel, JSONField, check_enum


T = TypeVar("T")

TOP_MEMBERS_PERCENT = 0.05

RECENT_PERIOD_DAYS = 30

YEAR_PERIOD_DAYS = 365

IS_NEW_PERIOD_DAYS = 20

UPVOTES_EXCLUDE_CHANNELS = [
    ClubChannelID.INTRO,
    ClubChannelID.ANNOUNCEMENTS,
    ClubChannelID.BOT,
    ClubChannelID.DASHBOARD,
    ClubChannelID.FUN,
    ClubChannelID.FUN_TOPICS,
    ClubChannelID.NEWCOMERS,
]

STATS_EXCLUDE_CHANNELS = [
    ClubChannelID.ANNOUNCEMENTS,
    ClubChannelID.JOBS,
    ClubChannelID.BOT,
    ClubChannelID.DASHBOARD,
    ClubChannelID.FUN,
    ClubChannelID.FUN_TOPICS,
    834443926655598592,  # práce-bot (archived)
]


@unique
class SubscriptionType(StrEnum):
    TRIAL = auto()
    MONTHLY = auto()
    YEARLY = auto()
    SPONSOR = auto()
    PARTNER = auto()
    FINAID = auto()
    FREE = auto()


class ClubUser(BaseModel):
    id = IntegerField(primary_key=True)
    account_id = IntegerField(null=True, unique=True)
    customer_id = CharField(null=True, unique=True)
    joined_at = DateTimeField(null=True)
    expires_at = DateTimeField(null=True)
    is_bot = BooleanField(default=False)
    is_member = BooleanField(default=True)
    has_avatar = BooleanField(default=True)
    avatar_path = CharField(null=True)
    display_name = CharField()
    has_feminine_name = BooleanField(null=True)
    mention = CharField(unique=True)
    coupon = CharField(null=True, index=True)
    initial_roles = JSONField(default=list)
    updated_roles = JSONField(null=True)
    dm_channel_id = IntegerField(null=True, unique=True)
    onboarding_channel_id = IntegerField(null=True, unique=True)
    total_spend = IntegerField(null=True)
    subscription_type = CharField(
        null=True, constraints=[check_enum("subscription_type", SubscriptionType)]
    )

    @property
    def joined_on(self) -> date | None:
        return self.joined_at.date() if self.joined_at else None

    @property
    def intro(self) -> Optional["ClubMessage"]:
        return (
            self.list_public_messages.where(
                ClubMessage.channel_id == ClubChannelID.INTRO,
                ClubMessage.type == "default",
            )
            .order_by(ClubMessage.created_at.desc())
            .first()
        )

    @property
    def list_public_messages(self) -> Iterable["ClubMessage"]:
        return self.list_messages.where(
            ClubMessage.is_private == False  # noqa: E712
        ).order_by(ClubMessage.created_at.desc())

    @property
    def intro_thread_id(self) -> int | None:
        intro = self.intro
        return intro.id if intro else None

    def update_expires_at(self, expires_at: datetime):
        self.expires_at = non_empty_max([self.expires_at, expires_at])

    def content_size(self, private: bool = False) -> int:
        list_messages = self.list_messages if private else self.list_public_messages
        return sum(message.content_size for message in list_messages)

    def recent_content_size(
        self, today=None, days=RECENT_PERIOD_DAYS, private=False
    ) -> int:
        messages = self.list_recent_messages(today, days=days, private=private)
        return sum(message.content_size for message in messages)

    def messages_count(self, private: bool = False) -> int:
        list_messages = self.list_messages if private else self.list_public_messages
        return list_messages.count()

    def upvotes_count(self, private: bool = False) -> int:
        list_messages = self.list_messages if private else self.list_public_messages
        messages = list_messages.where(
            ClubMessage.parent_channel_id.not_in(UPVOTES_EXCLUDE_CHANNELS)
        )
        return sum([message.upvotes_count for message in messages])

    def recent_upvotes_count(self, today=None, private=False) -> int:
        messages = self.list_recent_messages(today, private=private).where(
            ClubMessage.parent_channel_id.not_in(UPVOTES_EXCLUDE_CHANNELS)
        )
        return sum([message.upvotes_count for message in messages])

    def first_seen_on(self) -> date:
        first_message = self.list_messages.order_by(ClubMessage.created_at).first()
        if not first_message:
            first_pin = (
                self.list_pins.join(
                    ClubMessage, on=(ClubPin.pinned_message == ClubMessage.id)
                )
                .order_by(ClubMessage.created_at)
                .first()
            )
            first_message = first_pin.pinned_message if first_pin else None
        return first_message.created_at.date() if first_message else self.joined_on

    def list_recent_messages(
        self, today=None, days=RECENT_PERIOD_DAYS, private=False
    ) -> Iterable["ClubMessage"]:
        list_messages = self.list_messages if private else self.list_public_messages
        recent_period_start_at = (today or date.today()) - timedelta(days=days)
        return list_messages.where(
            ClubMessage.created_at >= recent_period_start_at
        ).order_by(ClubMessage.created_at.desc())

    def is_new(self, today=None) -> bool:
        return (self.first_seen_on() + timedelta(days=IS_NEW_PERIOD_DAYS)) >= (
            today or date.today()
        )

    @classmethod
    def get_member_by_id(cls, id: int) -> Self:
        return cls.members_listing().where(cls.id == id).get()

    @classmethod
    def count(cls) -> int:
        return cls.listing().count()

    @classmethod
    def members_count(cls) -> int:
        return cls.members_listing().count()

    @classmethod
    def avatars_count(cls) -> int:
        return cls.avatars_listing().count()

    @classmethod
    def feminine_names_count(cls) -> int:
        return (
            cls.members_listing()
            .where(cls.has_feminine_name == True)  # noqa: E712
            .count()
        )

    @classmethod
    def subscription_types_breakdown(cls) -> dict[str, int]:
        breakdown = {
            row.subscription_type: row.count
            for row in cls.select(
                cls.subscription_type,
                fn.COUNT(cls.id).alias("count"),
            )
            .where(
                cls.is_bot == False,  # noqa: E712
                cls.is_member == True,  # noqa: E712
            )
            .group_by(cls.subscription_type)
            .order_by(cls.subscription_type)
        }
        if None in breakdown:
            raise ValueError("Subscription type is not set for some members")
        return breakdown

    @classmethod
    def top_members_limit(cls) -> int:
        return math.ceil(cls.members_count() * TOP_MEMBERS_PERCENT)

    @classmethod
    def listing(cls) -> Iterable[Self]:
        return cls.select()

    @classmethod
    def members_listing(cls, shuffle=False) -> Iterable[Self]:
        members = cls.listing().where(
            cls.is_bot == False,  # noqa: E712
            cls.is_member == True,  # noqa: E712
        )
        if shuffle:
            members = members.order_by(fn.random())
        return members

    @classmethod
    def onboarding_listing(cls) -> Iterable[Self]:
        return cls.members_listing().where(cls.onboarding_channel_id.is_null(False))

    @classmethod
    def avatars_listing(cls) -> Iterable[Self]:
        return cls.members_listing().where(cls.avatar_path.is_null(False))


class ClubMessage(BaseModel):
    id = IntegerField(primary_key=True)
    url = CharField()
    content = TextField()
    content_size = IntegerField()
    content_starting_emoji = CharField(null=True, index=True)
    reactions = JSONField(default=dict)
    upvotes_count = IntegerField(default=0)
    downvotes_count = IntegerField(default=0)
    created_at = DateTimeField(index=True)
    created_month = CharField(index=True)
    author = ForeignKeyField(ClubUser, backref="list_messages")
    author_is_bot = BooleanField()
    channel_id = IntegerField(index=True)
    channel_name = CharField()
    parent_channel_id = IntegerField(index=True)
    parent_channel_name = CharField()
    category_id = IntegerField(index=True, null=True)
    type = CharField(default="default")
    is_private = BooleanField(default=False)
    pinned_message_url = IntegerField(null=True, index=True)
    ui_urls = JSONField(default=list)

    @property
    def is_pinning(self) -> bool:
        return bool(self.pinned_message_url)

    @property
    def is_intro(self) -> bool:
        return self.author.intro.id == self.id

    @property
    def is_starting_message(self) -> bool:
        return self.id == self.channel_id

    @property
    def dm_member(self) -> ClubUser:
        return ClubUser.get(dm_channel_id=self.channel_id)

    @property
    def pin(self) -> Optional["ClubPin"]:
        return self._pin.first()

    def record_pin(self):
        if not self.is_pinning:
            raise ValueError("Message is not a pinning message")
        pinned_message_id = parse_message_url(self.pinned_message_url)["message_id"]
        rows_count = (
            ClubPin.update({ClubPin.pinning_message: self})
            .where(
                ClubPin.pinned_message == pinned_message_id,
                ClubPin.member == self.dm_member,
            )
            .execute()
        )
        if rows_count != 1:
            raise ClubPin.DoesNotExist()

    @classmethod
    def count(cls) -> int:
        return cls.select().count()

    @classmethod
    def content_size_by_month(cls, date: date) -> int:
        messages = (
            cls.select()
            .where(cls.created_month == f"{date:%Y-%m}")
            .where(cls.author_is_bot == False)  # noqa: E712
            .where(cls.is_private == False)  # noqa: E712
            .where(cls.channel_id.not_in(STATS_EXCLUDE_CHANNELS))
        )
        return sum(message.content_size for message in messages)

    @classmethod
    def listing(cls) -> Iterable[Self]:
        return (
            cls.select()
            .where(cls.is_private == False)  # noqa: E712
            .order_by(cls.created_at)
        )

    @classmethod
    def pinning_listing(cls) -> Iterable[Self]:
        return (
            cls.select()
            .where(cls.pinned_message_url.is_null(False))
            .order_by(cls.created_at)
        )

    @classmethod
    def channel_listing(
        cls,
        channel_id: int,
        parent: bool = False,
        by_bot: bool = False,
        starting_emoji: str | None = None,
    ) -> Iterable[Self]:
        query = cls.select()
        if parent:
            query = query.where(cls.parent_channel_id == channel_id)
        else:
            query = query.where(cls.channel_id == channel_id)
        if by_bot:
            query = query.where(cls.author_is_bot == True)  # noqa: E712
        if starting_emoji:
            query = query.where(cls.content_starting_emoji == starting_emoji)
        return query.order_by(cls.created_at)

    # TODO squash with channel_listing
    @classmethod
    def channel_listing_since(cls, channel_id: int, since: datetime) -> Iterable[Self]:
        return (
            cls.select()
            .where((cls.channel_id == channel_id) & (cls.created_at >= since))
            .order_by(cls.created_at)
        )

    @classmethod
    def forum_listing(cls, channel_id: int) -> Iterable[Self]:
        return (
            cls.select()
            .where(cls.channel_id != channel_id, cls.parent_channel_id == channel_id)
            .group_by(cls.channel_id)
            .having(cls.id == fn.min(cls.id))
            .order_by(cls.created_at.desc())
        )

    @classmethod
    def digest_listing(cls, since: datetime, limit: int = 5) -> Iterable[Self]:
        return (
            cls.select()
            .where(
                cls.is_private == False,  # noqa: E712
                ClubMessage.parent_channel_id.not_in(UPVOTES_EXCLUDE_CHANNELS),
                cls.created_at >= since,
            )
            .order_by(cls.upvotes_count.desc())
            .limit(limit)
        )

    @classmethod
    def digest_channels(cls, since: datetime, limit: int = 5) -> Iterable[dict]:
        size = fn.sum(cls.content_size).alias("size")
        return (
            cls.select(
                size,
                cls.channel_id,
                cls.channel_name,
                cls.parent_channel_id,
                cls.parent_channel_name,
            )
            .where(
                cls.is_private == False,  # noqa: E712
                ClubMessage.parent_channel_id.not_in(UPVOTES_EXCLUDE_CHANNELS),
                cls.created_at >= since,
            )
            .group_by(cls.channel_id)
            .order_by(size.desc())
            .limit(limit)
            .dicts()
        )

    @classmethod
    def last_message(cls, channel_id: int | None = None) -> Self | None:
        query = cls.select()
        if channel_id is not None:
            query = query.where(cls.channel_id == channel_id)
        return query.order_by(cls.created_at.desc()).first()

    # TODO squash with last_message
    @classmethod
    def last_bot_message(
        cls,
        channel_id: int,
        starting_emoji: str | None = None,
        contains_text: str | None = None,
    ) -> Self | None:
        query = (
            cls.select()
            .where(
                cls.author_is_bot == True,  # noqa: E712
                cls.channel_id == channel_id,
            )
            .order_by(cls.created_at.desc())
        )
        if starting_emoji:
            query = query.where(cls.content_starting_emoji == starting_emoji)
        if contains_text:
            query = query.where(cls.content.contains(contains_text))
        return query.first()


class ClubPin(BaseModel):
    pinned_message = ForeignKeyField(ClubMessage, backref="list_pins")
    member = ForeignKeyField(ClubUser, backref="list_pins")
    pinning_message = ForeignKeyField(
        ClubMessage, backref="_pin", null=True, unique=True
    )

    @classmethod
    def count(cls):
        return cls.select().count()

    @classmethod
    def outstanding_by_member(cls, since: date):
        pins = (
            cls.select()
            .where(cls.pinning_message.is_null(True))
            .join(ClubMessage, on=(ClubPin.pinned_message == ClubMessage.id))
            .where(cls.pinned_message.created_at >= since)
            .join(ClubUser)
            .where(ClubUser.dm_channel_id.is_null(False))
            .order_by(ClubUser.id)
        )
        return groupby(pins, attrgetter("member"))

    @classmethod
    def honza_listing(cls):
        return (
            cls.select()
            .join(ClubUser)
            .switch(cls)
            .join(ClubMessage, on=(ClubPin.pinning_message_id == ClubMessage.id))
            .where(ClubUser.id == ClubMemberID.HONZA)
            .order_by(ClubMessage.created_at)
        )


def non_empty_min(values: Iterable[T | None]) -> T | None:
    values = list(filter(None, values))
    if values:
        return min(values)
    return None


def non_empty_max(values: Iterable[T | None]) -> T | None:
    values = list(filter(None, values))
    if values:
        return max(values)
    return None
