from peewee import BooleanField, CharField, ForeignKeyField, IntegerField, fn

from coop.models.base import BaseModel
from coop.models.club import ClubUser


class Mentor(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    company = CharField(null=True)
    bio_url = CharField(null=True)
    topics = CharField()
    book_url = CharField(null=True)
    message_url = CharField(unique=True, null=True)
    english_only = BooleanField(default=False)
    user = ForeignKeyField(ClubUser, unique=True)

    @classmethod
    def listing(cls):
        return (
            cls.select(cls, ClubUser)
            .join(ClubUser)
            .order_by(fn.lower(ClubUser.display_name))
        )

    @classmethod
    def interviews_listing(cls):
        return cls.listing().where(cls.topics.contains("pohovor"))
