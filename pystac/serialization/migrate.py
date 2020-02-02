import re
from copy import deepcopy

from pystac import STAC_VERSION
from pystac.extension import Extension
from pystac.serialization.identify import STACObjectType

# STAC Object Types


def _migrate_links(d, version):
    if version < '0.6':
        if 'links' in d:
            if isinstance(d['links'], dict):
                d['links'] = list(d['links'].values())


def _migrate_catalog(d, version, info):
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.common_extensions + info.custom_extensions


def _migrate_collection(d, version, info):
    _migrate_catalog(d, version, info)


def _migrate_item(d, version, info):
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.common_extensions + info.custom_extensions


def _migrate_itemcollection(d, version, info):
    return d


# Extensions


def _migrate_assets(d, version, info):
    pass


def _migrate_checksum(d, version, info):
    pass


def _migrate_datacube(d, version, info):
    pass


def _migrate_datetime_range(d, version, info):
    pass


def _migrate_eo(d, version, info):
    if version < '0.5':
        if 'eo:crs' in d['properties']:
            # Try to pull out the EPSG code.
            # Otherwise, just leave it alone.
            wkt = d['properties']['eo:crs']
            matches = list(re.finditer(r'AUTHORITY\[[^\]]*\"(\d+)"\]', wkt))
            if len(matches) > 0:
                epsg_code = matches[-1].group(1)
                d['properties'].pop('eo:crs')
                d['properties']['eo:epsg'] = int(epsg_code)

    if version < '0.6':
        # Change eo:bands from a dict to a list. eo:bands on an asset
        # is an index instead of a dict key. eo:bands is in properties.
        bands_dict = d['eo:bands']
        keys_to_indices = {}
        bands = []
        for i, (k, band) in enumerate(bands_dict.items()):
            keys_to_indices[k] = i
            bands.append(band)

        d.pop('eo:bands')
        d['properties']['eo:bands'] = bands
        for k, asset in d['assets'].items():
            if 'eo:bands' in asset:
                asset_band_indices = []
                for bk in asset['eo:bands']:
                    asset_band_indices.append(keys_to_indices[bk])
                asset['eo:bands'] = sorted(asset_band_indices)


def _migrate_label(d, version, info):
    pass


def _migrate_pointcloud(d, version, info):
    pass


def _migrate_sar(d, version, info):
    pass


def _migrate_scientific(d, version, info):
    pass


def _migrate_single_file_stac(d, version, info):
    pass


_object_migrations = {
    STACObjectType.CATALOG: _migrate_catalog,
    STACObjectType.COLLECTION: _migrate_collection,
    STACObjectType.ITEM: _migrate_item,
    STACObjectType.ITEMCOLLECTION: _migrate_itemcollection
}

_extension_migrations = {
    Extension.ASSETS: _migrate_assets,
    Extension.CHECKSUM: _migrate_checksum,
    Extension.DATACUBE: _migrate_datacube,
    Extension.DATETIME_RANGE: _migrate_datetime_range,
    Extension.EO: _migrate_eo,
    Extension.LABEL: _migrate_label,
    Extension.POINTCLOUD: _migrate_pointcloud,
    Extension.SAR: _migrate_sar,
    Extension.SCIENTIFIC: _migrate_scientific,
    Extension.SINGLE_FILE_STAC: _migrate_single_file_stac,
}


def migrate_to_latest(json_dict, info):
    """Migrates the STAC JSON to the latest version

    Args:
        json_dict (dict): The dict of STAC JSON to identify.
        info (STACJSONDescription): The info from
            :func:`~pystac.serialzation.identify.identify_stac_object` that describes
            the STAC object contained in the JSON dict.

    Returns:
        dict: A copy of the dict that is migrated to the latest version (the
        version that is pystac.STAC_VERSION)
    """
    result = deepcopy(json_dict)
    version = info.version_range.latest_valid_version()

    if version != STAC_VERSION:
        _object_migrations[info.object_type](result, version, info)

        for ext in info.common_extensions:
            _extension_migrations[ext](result, version, info)

    result['stac_version'] = STAC_VERSION

    return result
