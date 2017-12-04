# -*- coding: utf-8 -*-

"""Console script for pystac."""

import click
from .iserv.iserv import cli as iserv


@click.group()
def main(args=None):
    """Console script for pystac."""
    click.echo("Replace this message by putting your code into "
               "pystac.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")


main.add_command(iserv)

if __name__ == "__main__":
    main()
