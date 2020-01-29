class MediaType:
    """A list of common media types that can be used in STAC Asset and Link metadata.
    """
    TIFF = 'image/tiff'
    GEOTIFF = 'image/tiff; application=geotiff'
    COG = 'image/tiff; application=geotiff; profile=cloud-optimized'
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
