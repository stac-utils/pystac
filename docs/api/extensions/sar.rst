pystac.extensions.sar
=====================

Implements `SAR v1.3.2
<https://stac-extensions.github.io/sar/v1.3.2/schema.json>`_.
All fields are optional. SAR properties can be set on Items, Collection fields,
Item and Collection Assets, and Item Asset Definitions. Collection summaries
are available through :meth:`~pystac.extensions.sar.SarExtension.summaries`.

The extension includes range bandwidth in GHz, relative burst numbers starting
at 1, beam identifiers, and compact polarizations (LH, LV, RH, RV, CH, CV).
For example::

    from pystac.extensions.sar import Polarization, SarExtension

    sar = SarExtension.ext(item, add_if_missing=True)
    sar.apply(
        bandwidth=0.05,
        relative_burst=1,
        beam_ids=["IW1"],
        polarizations=[Polarization.RH, Polarization.RV],
    )

Unset fields return ``None``; assigning ``None`` removes a field. Existing
positional calls to ``apply`` remain supported. Center frequency and bandwidth
must be greater than zero. Use STAC validation to check schema constraints.

``sar:product_type`` is deprecated in favor of ``product:type``.
``sar:instrument_mode`` is deprecated in favor of ``instrument_modes`` from the
instruments extension. Both remain supported for compatibility.

.. automodule:: pystac.extensions.sar
   :members:
   :undoc-members:
