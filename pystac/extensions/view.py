from pystac import Extensions
from pystac.item import Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class ViewItemExt(ItemExtension):
    """ViewItemExt is the extension of the Item in the View Geometry Extension.
    View Geometry adds metadata related to angles of sensors and other radiance angles
    that affect the view of resulting data. It will often be combined with other extensions that
    describe the actual data, such as the eo, sat or sar extensions.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using ViewItemExt to directly wrap an item will add the 'view' extension ID to
        the item's stac_extensions.
    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.VIEW]
        elif Extensions.VIEW not in item.stac_extensions:
            item.stac_extensions.append(Extensions.VIEW)

        self.item = item

    def apply(self,
              off_nadir=None,
              incidence_angle=None,
              azimuth=None,
              sun_azimuth=None,
              sun_elevation=None):
        """Applies View Geometry extension properties to the extended Item.

        Args:
            off_nadir (float): The angle from the sensor between nadir (straight down)
                and the scene center. Measured in degrees (0-90).
            incidence_angle (float): The incidence angle is the angle between the vertical (normal)
                to the intercepting surface and the line of sight back to the satellite at
                the scene center. Measured in degrees (0-90).
            azimuth (float): Viewing azimuth angle. The angle measured from the sub-satellite
                point (point on the ground below the platform) between the scene center and true
                north. Measured clockwise from north in degrees (0-360).
            sun_azimuth (float): Sun azimuth angle. From the scene center point on the ground, this
                is the angle between truth north and the sun. Measured clockwise in degrees (0-360).
            sun_elevation (float): Sun elevation angle. The angle from the tangent of the scene
                center point to the sun. Measured from the horizon in degrees (0-90).
        """
        self.off_nadir = off_nadir
        self.incidence_angle = incidence_angle
        self.azimuth = azimuth
        self.sun_azimuth = sun_azimuth
        self.sun_elevation = sun_elevation

    @property
    def off_nadir(self):
        """Get or sets the angle from the sensor between nadir (straight down)
        and the scene center. Measured in degrees (0-90).

        Returns:
            [float]
        """
        return self.item.properties.get('view:off_nadir')

    @off_nadir.setter
    def off_nadir(self, v):
        self.item.properties['view:off_nadir'] = v

    @property
    def incidence_angle(self):
        """Get or sets the incidence angle is the angle between the vertical (normal)
        to the intercepting surface and the line of sight back to the satellite at
        the scene center. Measured in degrees (0-90).

        Returns:
            [float]
        """
        return self.item.properties.get('view:incidence_angle')

    @incidence_angle.setter
    def incidence_angle(self, v):
        self.item.properties['view:incidence_angle'] = v

    @property
    def azimuth(self):
        """Get or sets the viewing azimuth angle. The angle measured from the sub-satellite
        point (point on the ground below the platform) between the scene center and true
        north. Measured clockwise from north in degrees (0-360).

        Returns:
            [float]
        """
        return self.item.properties.get('view:azimuth')

    @azimuth.setter
    def azimuth(self, v):
        self.item.properties['view:azimuth'] = v

    @property
    def sun_azimuth(self):
        """Get or sets the sun azimuth angle. From the scene center point on the ground, this
        is the angle between truth north and the sun. Measured clockwise in degrees (0-360).

        Returns:
            [float]
        """
        return self.item.properties.get('view:sun_azimuth')

    @sun_azimuth.setter
    def sun_azimuth(self, v):
        self.item.properties['view:sun_azimuth'] = v

    @property
    def sun_elevation(self):
        """Get or sets the sun elevation angle. The angle from the tangent of the scene
        center point to the sun. Measured from the horizon in degrees (0-90).

        Returns:
            [float]
        """
        return self.item.properties.get('view:sun_elevation')

    @sun_elevation.setter
    def sun_elevation(self, v):
        self.item.properties['view:sun_elevation'] = v

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


VIEW_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.VIEW,
                                                [ExtendedObject(Item, ViewItemExt)])
