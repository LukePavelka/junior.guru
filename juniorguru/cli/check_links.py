import re
import time
from pathlib import Path
from subprocess import PIPE, Popen

import click

from juniorguru.cli.web import build as build_web


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) "
    "Gecko/20100101 Firefox/117.0"
)

EXCLUDE_URLS = [
    "*static/*.*",  # local links to static files
    "facebook.com/search/",  # HTTP_404 in response if user isn't logged in
    "juniorguru.memberful.com",  # HTTP_403, rightfully
    "support.discord.com",  # Discord ¯\_(ツ)_/¯
    "economist.com",  # crawling protection?
    "udemy.com",  # crawling protection?
    "att.jobs",  # crawling protection?
    "csob.cz",  # crawling protection?
    "fiverr.com",  # crawling protection?
    "twitter.com",  # crawling protection?
    "upwork.com",  # crawling protection?
    "docs.github.com",  # crawling protection?
    "make.com",  # crawling protection?
    "italki.com",  # crawling protection?
    "glassdoor.com",  # crawling protection?
    "oracle.com",  # crawling protection?
    "open.spotify.com",  # crawling protection?
    "startupjobs.cz/nabidka/",  # crawling protection?
    "datacamp.com",  # crawling protection?
    "meetup.com",  # crawling protection?
    "navolnenoze.cz",  # crawling protection?
    "robime.it",  # crawling protection?
    "reddit.com",  # crawling protection?
    "imysleni.cz",  # crawling protection?
]

EXCLUDE_REASONS = [
    re.compile(r)
    for r in [
        r"^BLC_UNKNOWN$",  # crawling protection?
        r"^ERRNO_EPROTO$",  # Czech TV website ¯\_(ツ)_/¯
        r"^ERRNO_ENOTFOUND$",  # crawling protection? can't even find the domain name
        r"^HTTP_999$",  # LinkedIn crawling protection
        r"^HTTP_429$",  # Twitter crawling protection, also https://github.com/stevenvachon/broken-link-checker/issues/198
        r"^HTTP_5\d\d$",  # server-side problem, can't do anything about that
        r"HTTP_undefined",  # :notsureif:
    ]
]


@click.command()
@click.argument(
    "output_path", default="public", type=click.Path(exists=True, path_type=Path)
)
@click.option("--build/--no-build", default=True)
@click.option("--retry/--no-retry", default=False)
@click.pass_context
def main(context, output_path, build, retry):
    if build:
        context.invoke(build_web, output_path=output_path)

    command = ["npx", "blcl"]
    options = [
        "--verbose",
        "--follow",
        "--recursive",
        "--get",  # because some sites return strange codes in response to HEAD :(
        f"--user-agent={USER_AGENT}",
    ]

    for url in EXCLUDE_URLS:
        options.append(f"--exclude={url}")

    # Internet is flaky... retrying 3 times makes us sure the problem is consistent
    attempts = 1
    if retry:
        attempts = 3

    broken = None
    failed = 1
    for attempt in range(attempts):
        print()
        print(f"Attempt #{attempt + 1} of {attempts}")
        print("=" * 79)
        broken = set()

        with Popen(
            command + options + [output_path],
            stdout=PIPE,
            bufsize=1,
            universal_newlines=True,
        ) as proc:
            for line in proc.stdout:
                print(line, end="")
                if "BROKEN" in line:
                    match = re.search(r"(http[^ \x1b]+)[^\(]+\(([^\)]+)\)", line)
                    broken.add((match.group(1), match.group(2)))

        failed = proc.returncode
        if failed:
            time.sleep(5)
        else:
            break

    # https://github.com/stevenvachon/broken-link-checker/issues/169
    if broken:
        warnings = []
        errors = []
        for url, reason in broken:
            relevant_list = None
            for reason_re in EXCLUDE_REASONS:
                if reason_re.search(reason):
                    relevant_list = warnings
                    break
            if relevant_list is None:
                relevant_list = errors
            relevant_list.append((url, reason))

        if warnings:
            print()
            print("Links not checked")
            print("=" * 79)
            for url, reason in warnings:
                print(f"{reason}\t{url}")

        if errors:
            print()
            print("Broken links")
            print("=" * 79)
            for url, reason in errors:
                print(f"{reason}\t{url}")

        if errors:
            raise click.Abort()
