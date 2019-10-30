class MediaType:
    """A list of common media types that can be used in STAC Asset and Link metadata.
    """
    TIFF = 'image/tiff'
    GEOTIFF = 'image/vnd.stac.geotiff'
    COG = 'image/vnd.stac.geotiff; cloud-optimized=true'
    JPEG2000 = 'image/jp2'
    PNG = 'image/png'
    JPEG = 'image/jpeg'
    XML = 'application/xml'
    JSON = 'application/json'
    TEXT = 'text/plain'
    GEOJSON = 'application/geo+json'
    GEOPACKAGE = 'application/geopackage+sqlite3'
    HDF5 = 'application/x-hdf5'  # Hierarchical Data Format version 5
    HDF = 'application/x-hdf'  # Hierarchical Data Format versions 4 and earlier.
