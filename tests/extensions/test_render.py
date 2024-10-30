"""Tests for pystac.tests.extensions.render"""

import json

import pytest

import pystac
import pystac.errors
from pystac.extensions.render import Render, RenderExtension
from tests.conftest import get_data_file


@pytest.fixture
def ext_collection_uri() -> str:
    return get_data_file("render/collection.json")


@pytest.fixture
def ext_collection(ext_collection_uri: str) -> pystac.Collection:
    return pystac.Collection.from_file(ext_collection_uri)


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("render/item.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


@pytest.fixture
def render() -> Render:
    return Render.create(
        assets=["B4", "B3", "B2"],
        title="RGB",
        rescale=[[0, 1000], [0, 1000], [0, 1000]],
        nodata=-9999,
        colormap_name="viridis",
        colormap={
            "0": "#e5f5f9",
            "10": "#99d8c9",
            "255": "#2ca25f",
        },
        color_formula="gamma rg 1.3, sigmoidal rgb 22 0.1, saturation 1.5",
        resampling="bilinear",
        expression="(B08-B04)/(B08+B04)",
        minmax_zoom=[2, 18],
    )


@pytest.fixture
def thumbnail_render(ext_item: pystac.Item) -> Render:
    return RenderExtension.ext(ext_item).renders["thumbnail"]


def test_collection_stac_extensions(ext_collection: pystac.Collection) -> None:
    assert RenderExtension.has_extension(ext_collection)


def test_item_stac_extensions(ext_item: pystac.Item) -> None:
    assert RenderExtension.has_extension(ext_item)


def test_ext_raises_if_item_does_not_conform(item: pystac.Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        RenderExtension.ext(item)


def test_ext_raises_if_collection_does_not_conform(
    collection: pystac.Collection,
) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        RenderExtension.ext(collection)


def test_ext_raises_on_catalog(catalog: pystac.Catalog) -> None:
    with pytest.raises(
        pystac.errors.ExtensionTypeError,
        match="RenderExtension does not apply to type 'Catalog'",
    ):
        RenderExtension.ext(catalog)  # type: ignore


def test_item_to_from_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert actual == d


def test_collection_to_from_dict(
    ext_collection_uri: str, ext_collection: pystac.Collection
) -> None:
    with open(ext_collection_uri) as f:
        d = json.load(f)
    actual = ext_collection.to_dict(include_self_link=False)
    assert actual == d


def test_add_to_item(item: pystac.Item) -> None:
    assert not RenderExtension.has_extension(item)
    RenderExtension.add_to(item)

    assert RenderExtension.has_extension(item)


def test_add_to_collection(collection: pystac.Collection) -> None:
    assert not RenderExtension.has_extension(collection)
    RenderExtension.add_to(collection)

    assert RenderExtension.has_extension(collection)


# TODO: re-enable, record cassette after schema is corrected
# @pytest.mark.vcr
# def test_item_validate(ext_item: pystac.Item) -> None:
#     assert ext_item.validate()


# @pytest.mark.vcr
# def test_collection_validate(ext_collection: pystac.Collection) -> None:
#     assert ext_collection.validate()


def test_get_render_values(thumbnail_render: Render) -> None:
    assert thumbnail_render.title == "Thumbnail"
    assert thumbnail_render.assets == ["B04", "B03", "B02"]
    assert thumbnail_render.rescale == [[0, 150]]
    assert thumbnail_render.colormap_name == "rainbow"
    assert thumbnail_render.resampling == "bilinear"
    # assert thumbnail_render.bidx == [1]
    # assert thumbnail_render.width == 1024
    # assert thumbnail_render.height == 1024
    # assert thumbnail_render.bands == ["B4", "B3", "B2"]


def test_apply_renders_to_item(item: pystac.Item, render: Render) -> None:
    RenderExtension.add_to(item)

    RenderExtension.ext(item).apply({"render": render})
    assert item.ext.render.renders["render"].assets == ["B4", "B3", "B2"]
    assert item.ext.render.renders["render"].title == "RGB"
    assert item.ext.render.renders["render"].rescale == [
        [0, 1000],
        [0, 1000],
        [0, 1000],
    ]
    assert item.ext.render.renders["render"].nodata == -9999
    assert item.ext.render.renders["render"].colormap_name == "viridis"
    assert item.ext.render.renders["render"].colormap == {
        "0": "#e5f5f9",
        "10": "#99d8c9",
        "255": "#2ca25f",
    }
    assert (
        item.ext.render.renders["render"].color_formula
        == "gamma rg 1.3, sigmoidal rgb 22 0.1, saturation 1.5"
    )
    assert item.ext.render.renders["render"].resampling == "bilinear"
    assert item.ext.render.renders["render"].expression == "(B08-B04)/(B08+B04)"
    assert item.ext.render.renders["render"].minmax_zoom == [2, 18]

    assert item.ext.render.renders["render"] == render


def test_get_unset_properties(item: pystac.Item) -> None:
    RenderExtension.add_to(item)
    RenderExtension.ext(item).apply(
        {
            "render": Render.create(
                assets=["B4", "B3", "B2"],
            )
        }
    )

    assert item.ext.render.renders["render"].title is None
    assert item.ext.render.renders["render"].rescale is None
    assert item.ext.render.renders["render"].nodata is None
    assert item.ext.render.renders["render"].colormap_name is None
    assert item.ext.render.renders["render"].colormap is None
    assert item.ext.render.renders["render"].color_formula is None
    assert item.ext.render.renders["render"].resampling is None
    assert item.ext.render.renders["render"].expression is None
    assert item.ext.render.renders["render"].minmax_zoom is None


def test_equality_check_with_unexpected_type_raises_notimplemented_error() -> None:
    render = Render.create(
        assets=["B4", "B3", "B2"],
    )
    with pytest.raises(NotImplementedError):
        _ = render == 1


def test_item_repr(ext_item: pystac.Item) -> None:
    ext = RenderExtension.ext(ext_item)
    assert ext.__repr__() == f"<ItemRenderExtension Item id={ext_item.id}>"


def test_collection_repr(ext_collection: pystac.Collection) -> None:
    ext = RenderExtension.ext(ext_collection)
    assert (
        ext.__repr__()
        == f"<CollectionRenderExtension Collection id={ext_collection.id}>"
    )


def test_render_repr() -> None:
    render = Render.create(
        assets=["B4", "B3", "B2"],
        title="RGB",
        rescale=[[0, 1000], [0, 1000], [0, 1000]],
        nodata=-9999,
        colormap_name="viridis",
        colormap={
            "0": "#e5f5f9",
            "10": "#99d8c9",
            "255": "#2ca25f",
        },
        color_formula="gamma rg 1.3, sigmoidal rgb 22 0.1, saturation 1.5",
        resampling="bilinear",
        expression="(B08-B04)/(B08+B04)",
        minmax_zoom=[2, 18],
    )

    assert render.__repr__() == (
        "<Render assets=['B4', 'B3', 'B2'] "
        "title=RGB rescale=[[0, 1000], [0, 1000], [0, 1000]] "
        "nodata=-9999 colormap_name=viridis "
        "colormap={'0': '#e5f5f9', '10': '#99d8c9', '255': '#2ca25f'} "
        "color_formula=gamma rg 1.3, sigmoidal rgb 22 0.1, saturation 1.5 "
        "resampling=bilinear expression=(B08-B04)/(B08+B04) minmax_zoom=[2, 18]>"
    )
