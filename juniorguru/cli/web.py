import hashlib
import shutil
import subprocess
import warnings
from functools import cache, wraps
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import click
from livereload import Server
from lxml import html
from mkdocs.__main__ import build_command as _build_mkdocs

from juniorguru.lib import loggers
from juniorguru.web_legacy.__main__ import main as flask_freeze


logger = loggers.from_path(__file__)


@click.group()
def main():
    pass


def building(title: str):
    def decorator(command):
        @wraps(command)
        def wrapper(*args, **kwargs):
            time_start = perf_counter()
            logger.info(f"Building {title}")
            return_value = command(*args, **kwargs)
            time_end = perf_counter() - time_start
            logger.info(f"Done building {title} in {time_end:.2f}s")
            return return_value

        return wrapper

    return decorator


@main.command()
@click.argument("output_path", default="public", type=click.Path(path_type=Path))
@building("static files")
def build_static(output_path: Path):
    static_path = output_path / "static"
    shutil.copytree(
        "juniorguru/images",
        static_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("screenshots-overrides"),
    )
    shutil.copytree(
        "juniorguru/images/screenshots-overrides",
        static_path / "screenshots",
        dirs_exist_ok=True,
    )
    subprocess.run(["node", "esbuild.js", str(static_path.absolute())], check=True)
    Path(static_path / "favicon.ico").rename(output_path / "favicon.ico")


@main.command()
@click.argument("output_path", default="public", type=click.Path(path_type=Path))
@building("Flask files")
def build_flask(output_path: Path):
    flask_freeze(output_path)


@main.command()
@click.pass_context
@click.argument("output_path", default="public", type=click.Path(path_type=Path))
@click.argument(
    "config",
    default="juniorguru/web/mkdocs.yml",
    type=click.Path(exists=True, path_type=Path),
)
@click.option("-w", "--warnings/--no-warnings", "warn", default=False)
@building("MkDocs files")
def build_mkdocs(context, config: Path, output_path: Path, warn: bool):
    _simplefilter = warnings.simplefilter
    if not warn:
        # Unfortunately MkDocs sets their own warnings filter, so we have to
        # nuke the whole thing to disable warnings. This is a hack, but it works.
        warnings.simplefilter = lambda *args, **kwargs: None

    # Unfortunately MkDocs doesn't support mixing with existing files inside
    # the output directory, so we have to build into a temporary directory and
    # then move the files over manually.
    with TemporaryDirectory() as temp_dir:
        try:
            context.invoke(
                _build_mkdocs, config_file=str(config.absolute()), site_dir=temp_dir
            )
            shutil.copytree(
                temp_dir,
                output_path.absolute(),
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("sitemap.xml*"),
            )
        finally:
            warnings.simplefilter = _simplefilter


@main.command()
@click.argument("output_path", default="public", type=click.Path(path_type=Path))
@click.pass_context
@building("everything")
def build(context, output_path: Path):
    shutil.rmtree(output_path, ignore_errors=True)
    output_path.mkdir(parents=True, exist_ok=True)
    context.invoke(build_static, output_path=output_path)
    context.invoke(build_flask, output_path=output_path)
    context.invoke(build_mkdocs, output_path=output_path)


@main.command()
@click.argument("output_path", default="public", type=click.Path(path_type=Path))
@click.option("--open/--no-open", default=False)
@click.pass_context
def serve(context, output_path: Path, open: bool):
    context.invoke(build, output_path=output_path)

    def ignore_data(path) -> bool:
        return Path(path).suffix in [".db-shm", ".db-wal", ".log"]

    def rebuild_static():
        context.invoke(build_static, output_path=output_path)

    @building("Flask and MkDocs files")
    def rebuild_flask_and_mkdocs():
        subprocess.run(["jg", "web", "build-flask", str(output_path)], check=True)
        subprocess.run(["jg", "web", "build-mkdocs", str(output_path)], check=True)

    def rebuild_mkdocs():
        subprocess.run(["jg", "web", "build-mkdocs", str(output_path)], check=True)

    server = Server()
    server.setHeader("Access-Control-Allow-Origin", "*")
    server.watch("juniorguru/**/*.js", rebuild_static)
    server.watch("juniorguru/**/*.scss", rebuild_static)
    server.watch("juniorguru/images/", rebuild_static)
    server.watch("juniorguru/data/", rebuild_flask_and_mkdocs, ignore=ignore_data)
    server.watch("juniorguru/lib/", rebuild_flask_and_mkdocs)
    server.watch("juniorguru/models/", rebuild_flask_and_mkdocs)
    server.watch("juniorguru/web/", rebuild_mkdocs)
    server.watch("juniorguru/web_legacy/", rebuild_flask_and_mkdocs)
    server.serve(
        host="localhost",
        root=str(output_path.absolute()),
        open_url_delay=0.1 if open else None,
    )


@main.command()
@click.argument(
    "output_path", default="public", type=click.Path(exists=True, path_type=Path)
)
def post_process(output_path: Path):
    for html_path in output_path.glob("**/*.html"):
        logger["postprocess"].info(f"Post-processing {html_path}")
        html_tree = html.fromstring(html_path.read_text())

        # Cache busting CSS
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#cache_busting
        for link in html_tree.cssselect('link[href$=".css"]'):
            href = link.get("href")
            try:
                css_path = resolve_path(output_path, html_path, href)
            except ValueError as e:
                logger["postprocess"].debug(str(e))
            else:
                logger["postprocess"].debug(f"Cache busting {href} ({css_path})")
                href = f"{href}?hash={hash_file(css_path)}"
                link.set("href", href)

        # Cache busting JS
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#cache_busting
        for script in html_tree.cssselect('script[src$=".js"]'):
            src = script.get("src")
            try:
                js_path = resolve_path(output_path, html_path, src)
            except ValueError as e:
                logger["postprocess"].debug(str(e))
            else:
                logger["postprocess"].debug(f"Cache busting {src} ({js_path})")
                src = f"{src}?hash={hash_file(js_path)}"
                script.set("src", src)

        # Hyphenation
        # https://github.com/ytiurin/hyphen
        for document in html_tree.cssselect(".document"):
            document_bytes = html.tostring(document, encoding="unicode").encode("utf-8")
            result = subprocess.run(
                ["node", "juniorguru/js/hyphenate.cjs"],
                input=document_bytes,
                stdout=subprocess.PIPE,
                check=True,
            )
            hyphenated_document = html.fromstring(result.stdout.decode("utf-8"))
            document.getparent().replace(document, hyphenated_document)

        html_path.write_text(html.tostring(html_tree, encoding="unicode"))


def resolve_path(output_path: Path, html_path: Path, url: str):
    if url.startswith("http"):
        raise ValueError(f"Cannot resolve external URL: {url}")
    if url.startswith("/"):
        return (output_path / url.lstrip("/")).resolve()
    return (html_path.parent / url).resolve()


@cache
def hash_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()
