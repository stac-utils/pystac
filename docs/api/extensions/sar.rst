pystac.extensions.sar
=====================

See the :stac-ext:`SAR Extension <sar>` for more information about the fields.

For example::

    from pystac.extensions.sar import Polarization, SarExtension

    sar = SarExtension.ext(item, add_if_missing=True)
    sar.apply(
        bandwidth=0.05,
        relative_burst=1,
        beam_ids=["IW1"],
        polarizations=[Polarization.RH, Polarization.RV],
    )

.. automodule:: pystac.extensions.sar
   :members:
   :undoc-members:
