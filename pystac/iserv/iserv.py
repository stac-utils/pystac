"""Creates a data/tile footprint"""
from datetime import datetime
import logging
import os

import click
import rasterio
from dateutil.parser import parse

from pystac.iserv.footprint import generate_thumbnail, extract_footprint
from pystac.models import (
    Feature,
    Product,
    Band,
    Asset,
    Link,
    Properties
)
from pystac.utils.io import list_files_prefix

logger = logging.getLogger(__name__)


@click.group(name='iserv')
def cli():
    click.echo("Process ISERV data and assets")


def create_asset(filepath: str, is_relative: bool, product: str) -> Asset:
    if is_relative:
        _, href = os.path.split(filepath)
    else:
        href = filepath

    file_extension = filepath.split('.')[-1].lower()
    if file_extension == 'tif':
        file_format = 'tif'
        name = 'RGB Tif'
    elif file_extension == 'jpg':
        file_format = 'jpg'
        name = 'RGB JPEG'
    else:
        file_format = ''
        name = ''
        product = ''
    return Asset(href, file_format, product, name)


def get_properties(tif_path: str, iserv_prefix: str) -> Properties:
    """Extracts properties of a tif by parsing EXIF tags

    Args:
        tif_path (str): path to tif file
        iserv_prefix (str): used as a fallback if exif datetime tag is missing
    """

    with rasterio.open(tif_path) as src:
        tags = src.tags()
    datetime_tag = tags.get('EXIF_DateTime')
    if datetime_tag:
        datetime_start = datetime_end = parse(datetime_tag)
    else:
        year = int(iserv_prefix[3:7])
        month = int(iserv_prefix[7:9])
        day = int(iserv_prefix[9:11])
        datetime_end = datetime_start = datetime(year, month, day)
    imagery_license = 'CC0'
    provider = 'NASA, ISERV'
    return Properties(datetime_start, datetime_end, provider, imagery_license)


@click.command(name='write-product')
@click.argument('filepath')
def write_product(filepath: str) -> Product:
    """Writes ISERV product definition to filepath"""

    iserv_bands = [
        Band('Red', 5.6, 450, 100, 1),
        Band('Green', 5.6, 550, 100, 2),
        Band('Blue', 5.6, 700, 100, 3),
    ]

    iserv_product = Product(
        'iserv-raw-rgb',
        iserv_bands,
        'geotiff',
        'ISERV/NASA'
    )

    with open(filepath, 'w') as fh:
        fh.write(iserv_product.json)

    return iserv_product


@click.command(name='create-feature')
@click.argument('directory')
@click.argument('prefix')
@click.argument('product')
@click.option('--relative/--absolute', default=True,
              help='whether assets should be referenced with relative or absolute paths')
@click.option('--self-override-directory',
              help='overrides directory when creating absolute self URL, useful when generating' +
              'a remote asset catalog')
def create_feature(directory: str, prefix: str, product: str, relative: bool = True,
                   self_override_directory: str = None) -> Feature:
    """Creates a STAC feature of iserv data given a directory, prefix, and product

    \b
    Args:
        directory (str): location of ISERV data
        prefix (str): prefix of ISERV data (e.g. IP0201306202030583203N09762W)
        product (str): URI of product definition for ISERV data
        relative (bool): whether assets should be referenced with relative or absolute paths
        self_override_directory (str): override directory when generating self link for asset
    """

    files = list_files_prefix(directory, prefix)
    tif_path = [f for f in files if f.endswith('.TIF')][0]
    geometry = extract_footprint(tif_path)
    assets = [create_asset(f, relative, product) for f in files if not f.endswith('.json')]

    if self_override_directory:
        self_location = os.path.join(self_override_directory, prefix + '.json')
    else:
        self_location = os.path.join(directory, prefix + '.json')
    self_link = Link('self', self_location)

    thumbnail_path = generate_thumbnail(prefix, tif_path)
    _, thumbnail_location = os.path.split(thumbnail_path)
    thumbnail_link = Link('thumbnail', thumbnail_location)
    links = [self_link, thumbnail_link]

    properties = get_properties(tif_path, prefix)
    feature = Feature(prefix, geometry, properties, links, assets)

    feature_location = os.path.join(directory, prefix + '.json')
    with open(feature_location, 'w') as fh:
        fh.write(feature.json)
    return feature


cli.add_command(write_product)
cli.add_command(create_feature)
