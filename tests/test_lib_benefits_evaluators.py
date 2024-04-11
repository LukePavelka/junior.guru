from datetime import date

import pytest

from jg.core.lib.benefits_evaluators import evaluate_members
from jg.core.models.club import ClubUser
from jg.core.models.partner import Partner, Partnership

from testing_utils import prepare_partner_data, prepare_test_db


@pytest.fixture
def test_db():
    yield from prepare_test_db([Partner, Partnership, ClubUser])


@pytest.mark.parametrize(
    "members_count, expected",
    [
        (0, False),
        (1, True),
        (10, True),
    ],
)
def test_evaluate_members(test_db, members_count, expected):
    partner = Partner.create(**prepare_partner_data(1))
    partnership = Partnership.create(partner=partner, starts_on=date(2023, 3, 16))
    for id in range(members_count):
        ClubUser.create(
            id=id,
            display_name=f"Jane{id}",
            mention=f"<@{id}>",
            coupon=partner.coupon,
        )

    assert evaluate_members(partnership) is expected
