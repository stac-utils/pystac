from pystac.utils import StringEnum


class MediaType(StringEnum):
    """A list of common media types that can be used in STAC Asset and Link metadata."""

    COG = "image/tiff; application=geotiff; profile=cloud-optimized"
    FLATGEOBUF = "application/vnd.flatgeobuf"  # https://github.com/flatgeobuf/flatgeobuf/discussions/112#discussioncomment-4606721  # noqa
    GEOJSON = "application/geo+json"
    GEOPACKAGE = "application/geopackage+sqlite3"
    GEOTIFF = "image/tiff; application=geotiff"
    HDF = "application/x-hdf"  # Hierarchical Data Format versions 4 and earlier.
    HDF5 = "application/x-hdf5"  # Hierarchical Data Format version 5
    HTML = "text/html"
    JPEG = "image/jpeg"
    JPEG2000 = "image/jp2"
    JSON = "application/json"
    PARQUET = "application/x-parquet"  # https://github.com/opengeospatial/geoparquet/issues/115#issuecomment-1181549523
    PNG = "image/png"
    TEXT = "text/plain"
    TIFF = "image/tiff"
    KML = "application/vnd.google-earth.kml+xml"
    XML = "application/xml"
    PDF = "application/pdf"
    ZARR = "application/vnd+zarr"  # https://github.com/openMetadataInitiative/openMINDS_core/blob/v4/instances/data/contentTypes/zarr.jsonld
    NETCDF = "application/netcdf"  # https://github.com/Unidata/netcdf/issues/42#issuecomment-1007618822


#: Media types that can be resolved as STAC Objects
STAC_JSON = [None, MediaType.GEOJSON, MediaType.JSON]
