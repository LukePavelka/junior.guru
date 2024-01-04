import re

from juniorguru.sync.jobs_scraped.processing import DropItem


BLOCKLIST = [
    ("title", re.compile(r"\b(plc|cnc) programátor", re.I)),
    ("title", re.compile(r"elektro", re.I)),
    ("title", re.compile(r"\bkonstruktér", re.I)),
    ("title", re.compile(r"\boperátor výroby", re.I)),
    ("title", re.compile(r"\bcae inženýr", re.I)),
    ("title", re.compile(r"\bseřizovač", re.I)),
    ("title", re.compile(r"manažer úspěchu", re.I)),
    ("company_name", re.compile(r"Advantage Consulting", re.I)),
    ("company_name", re.compile(r"Hitachi Energy", re.I)),
    ("company_name", re.compile(r"SPORTISIMO", re.I)),
    ("company_name", re.compile(r"Jobs Contact Personal", re.I)),
]


def process(item):
    for field, value_re in BLOCKLIST:
        value = item.get(field) or ""
        if value_re.search(value):
            raise DropItem(
                f"Blocklist rule applied: {field} value {value!r} matches {value_re.pattern!r}"
            )
    return item
