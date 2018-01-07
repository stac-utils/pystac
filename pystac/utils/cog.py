import subprocess


def generate_cog(source_filepath: str, dest_filepath: str):
    """Generates a Cloud Optimized Geotiff (COG) using GDAL

    Args:
        source_filepath (str): source tif to generate COG for
        dest_filepath (str): destination COG
    """

    overview_command = ['gdaladdo', source_filepath, '2 4 8 16 32']
    translate_command = ['gdal_translate', source_filepath, dest_filepath, '-co', 'TILED=YES', '-co', 'COMPRESS=LZW',
                         '-co', 'COPY_SRC_OVERVIEWS=YES']

    subprocess.check_call(overview_command)
    subprocess.check_call(translate_command)
