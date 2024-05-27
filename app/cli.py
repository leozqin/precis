from os import PathLike
from pathlib import Path

import asyncclick as click

from app.app import rss


@click.group
def cli():
    pass


@cli.command()
async def backup():
    """
    Write a json-format backup of the current Precis state
    to stdout. The file will also be saved in DATA_DIR.
    """
    file_path, _ = await rss.backup()

    with open(file_path, "r") as fp:
        bk = fp.read()

    click.echo(bk)


@cli.command()
@click.argument("file_path")
async def restore(file_path: PathLike):
    """
    Restore a json-format backup of the Precis state
    """
    with open(Path(file_path).resolve(), "r") as fp:
        await rss.restore(fp)


@cli.command()
async def export_opml():
    """
    Write a opml-format list of the feeds configured in Precis
    to stdout. The file will also be saved in DATA_DIR.
    """
    file_path, _ = await rss.feeds_to_opml()

    with open(file_path, "r") as fp:
        bk = fp.read()

    click.echo(bk)


@cli.command()
@click.argument("file_path")
async def import_opml(file_path: PathLike):
    """
    Import an opml-formatted feed list into Precis
    """
    with open(Path(file_path).resolve(), "r") as fp:
        await rss.opml_to_feeds(fp)
