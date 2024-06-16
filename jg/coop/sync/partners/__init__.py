from collections import defaultdict
from datetime import date
from pathlib import Path

import click
from strictyaml import Bool, Map, Optional, Seq, Str, Url, load

from jg.coop.cli.sync import main as cli
from jg.coop.lib import loggers
from jg.coop.lib.coupons import parse_coupon
from jg.coop.lib.images import PostersCache, render_image_file
from jg.coop.lib.memberful import MemberfulAPI
from jg.coop.lib.yaml import Date
from jg.coop.models.base import db
from jg.coop.models.partner import Partner, Partnership, PartnershipPlan


logger = loggers.from_path(__file__)


YAML_PATH = Path("jg/coop/data/partners.yml")

YAML_SCHEMA = Seq(
    Map(
        {
            "name": Str(),
            "slug": Str(),
            "url": Url(),
            "partnerships": Seq(
                Map(
                    {
                        "plan": Str(),
                        "starts_on": Date(),
                        Optional("expires_on"): Date(),
                        Optional("benefits"): Seq(
                            Map(
                                {
                                    "slug": Str(),
                                    Optional("done"): Url() | Bool(),
                                }
                            )
                        ),
                        Optional("agreements"): Seq(
                            Map(
                                {
                                    "text": Str(),
                                    Optional("done"): Url() | Bool(),
                                }
                            )
                        ),
                    }
                ),
            ),
        }
    )
)

COUPONS_GQL_PATH = Path(__file__).parent / "coupons.gql"

IMAGES_DIR = Path("jg/coop/images")

LOGOS_DIR = IMAGES_DIR / "logos"

POSTERS_DIR = IMAGES_DIR / "posters-sponsors"

POSTER_WIDTH = 700

POSTER_HEIGHT = 700


@cli.sync_command(dependencies=["partnership-plans"])
@click.option("--clear-posters/--keep-posters", default=False)
@db.connection_context()
def main(clear_posters):
    posters = PostersCache(POSTERS_DIR)
    posters.init(clear=clear_posters)

    logger.info("Getting coupons data from Memberful")
    memberful = MemberfulAPI()
    coupons_mapping = get_coupons_mapping(
        memberful.get_nodes(COUPONS_GQL_PATH.read_text())
    )

    logger.info("Reading YAML with partners")
    yaml_records = (record.data for record in load(YAML_PATH.read_text(), YAML_SCHEMA))

    logger.info("Setting up events db tables")
    db.drop_tables([Partner, Partnership])
    db.create_tables([Partner, Partnership])

    logger.info("Processing YAML records")
    for yaml_record in yaml_records:
        partnerships = yaml_record.pop("partnerships")

        logo_path = LOGOS_DIR / f"{yaml_record['slug']}.svg"
        if not logo_path.exists():
            logo_path = logo_path.with_suffix(".png")
        if not logo_path.exists():
            raise FileNotFoundError(
                f"'There is no {yaml_record['slug']}.svg or .png inside {LOGOS_DIR}"
            )

        partner = Partner.create(
            logo_path=logo_path.relative_to(IMAGES_DIR),
            **yaml_record,
            **coupons_mapping.get(yaml_record["slug"], {}),
        )
        for partnership in partnerships:
            try:
                plan_slug = partnership.pop("plan")
                logger.info(
                    f"Creating {partner.name} partnership with plan {plan_slug!r}"
                )
                plan = PartnershipPlan.get_by_slug(plan_slug)
                plan_benefits_slugs = plan.benefits_slugs()
                partnership["plan"] = plan
            except PartnershipPlan.DoesNotExist:
                if (
                    not partnership["expires_on"]
                    or partnership["expires_on"] > date.today()
                ):
                    raise
                logger.warning(
                    f"Expired {partner.name} partnership has non-existing plan: {plan_slug}"
                )
            else:
                partnership["benefits_registry"] = []
                for benefit in partnership.pop("benefits", []):
                    if benefit["slug"] not in plan_benefits_slugs:
                        logger.warning(
                            f"Plan {plan_slug!r} doesn't have benefit {benefit['slug']!r}, but {partner.name} has it specified"
                        )
                    partnership["benefits_registry"].append(benefit)

                partnership["agreements_registry"] = []
                for agreement in partnership.pop("agreements", []):
                    partnership["agreements_registry"].append(agreement)
            Partnership.create(partner=partner, **partnership)

    for partnership in Partnership.active_listing():
        partner = partnership.partner
        logger.info(f"Rendering poster for {partner.name}")
        tpl_context = dict(partner=partner)
        image_path = render_image_file(
            POSTER_WIDTH,
            POSTER_HEIGHT,
            "partner.jinja",
            tpl_context,
            POSTERS_DIR,
            prefix=partner.slug,
        )
        partner.poster_path = image_path.relative_to(IMAGES_DIR)
        partner.save()
        posters.record(IMAGES_DIR / partner.poster_path)
    posters.cleanup()

    logger.info("Checking expired partnerships for leftovers")
    for partner in Partner.expired_listing():
        logo_path = IMAGES_DIR / partner.logo_path
        if logo_path.exists():
            logger.warning(
                f"File {logo_path} is probably redundant, partnership with {partner.name} expired"
            )


def get_coupons_mapping(coupons):
    coupons_mapping = defaultdict(dict)
    for coupon in coupons:
        if coupon["state"] == "enabled":
            parts = parse_coupon(coupon["code"])
            slug = parts["slug"].lower()
            coupons_mapping[slug]["coupon"] = coupon["code"]
    return dict(coupons_mapping)
