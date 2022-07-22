from pystac.utils import StringEnum


class MediaType(StringEnum):
    """A list of common media types that can be used in STAC Asset and Link metadata."""

    COG = "image/tiff; application=geotiff; profile=cloud-optimized"
    GEOJSON = "application/geo+json"
    GEOPACKAGE = "application/geopackage+sqlite3"
    GEOTIFF = "image/tiff; application=geotiff"
    HDF = "application/x-hdf"  # Hierarchical Data Format versions 4 and earlier.
    HDF5 = "application/x-hdf5"  # Hierarchical Data Format version 5
    HTML = "text/html"
    JPEG = "image/jpeg"
    JPEG2000 = "image/jp2"
    JSON = "application/json"
    PNG = "image/png"
    TEXT = "text/plain"
    TIFF = "image/tiff"
    XML = "application/xml"
    PDF = "application/pdf"
