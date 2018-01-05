"""Creates a data/tile footprint"""
import json
import logging
import os
import subprocess
import tempfile

import rasterio
from geojson import Polygon

from pystac.utils.io import get_tempdir

logger = logging.getLogger(__name__)


def generate_thumbnail(prefix: str, tif_path: str) -> str:
    """Generates thumbnail for ISERV data using GDAL

    Args:
        prefix (str): prefix of ISERV data (used when generating thumbnail filename)
        tif_path (str): URI of tif, used when writing tif file
    """

    with get_tempdir() as temp_dir:
        logger.info('Beginning process to extract footprint for image:%s', tif_path)
        _, base_path = tempfile.mkstemp(dir=temp_dir)
        resampled_tif_path = base_path + '-resampled.tif'
        warped_tif_path = base_path + '-warped.tif'

        # thumbnail needs a more permanent home
        thumbnail_dir, _ = os.path.split(tif_path)
        thumbnail_path = os.path.join(thumbnail_dir, prefix + '.png')

        with rasterio.open(tif_path) as src:
            y, x = src.shape
            aspect = y / float(x)
            x_size = 512
            y_size = int(512 * aspect)

        resample_cmd = ['gdal_translate', tif_path, resampled_tif_path, '-outsize',
                        str(x_size), str(y_size)]
        warp_cmd = ['gdalwarp', '-dstnodata', '0', '-dstalpha', '-t_srs', 'epsg:3857',
                    resampled_tif_path, warped_tif_path]
        thumbnail_cmd = ['gdal_translate', '-of', 'PNG', warped_tif_path, thumbnail_path]
        subprocess.check_call(resample_cmd)
        subprocess.check_call(warp_cmd)
        subprocess.check_call(thumbnail_cmd)

    return thumbnail_path


def extract_footprint(tif_path: str) -> Polygon:
    """Performs all actions to extract polygon from an ISERV scene

    Args:
        tif_path (str): path to tif to extract polygons from

    Returns:
        Polygon
    """
    with get_tempdir() as temp_dir:
        logger.info('Beginning process to extract footprint for image:%s', tif_path)
        _, base_path = tempfile.mkstemp(dir=temp_dir)
        resampled_tif_path = base_path + '-resampled.tif'
        warped_path = base_path + '-warped.tif'
        geojson_path = base_path + '.geojson'

        with rasterio.open(tif_path) as src:
            y, x = src.shape
            aspect = y / float(x)
            x_size = 512
            y_size = int(512 * aspect)

        resample_cmd = ['gdal_translate', tif_path, resampled_tif_path, '-outsize',
                        str(x_size), str(y_size)]
        warp_cmd = ['gdalwarp', '-co', 'compress=LZW', '-dstnodata', '0', '-dstalpha',
                    '-t_srs', 'epsg:4326', resampled_tif_path, warped_path]
        polygonize_cmd = ['gdal_polygonize.py', '-b', '4', warped_path, '-f',
                          'GEOJSON', geojson_path]

        subprocess.check_call(resample_cmd)
        subprocess.check_call(warp_cmd)
        subprocess.check_call(polygonize_cmd)
        with open(geojson_path, 'r+') as fh:
            geojson = json.load(fh)

    return Polygon(geojson['features'][0]['geometry']['coordinates'])
