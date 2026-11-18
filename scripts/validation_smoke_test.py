from pystac.validation import validate_dict


def main() -> None:
    validate_dict(
        {
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [
                "https://stac-extensions.github.io/projection/v2.0.0/schema.json"
            ],
            "id": "x",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "bbox": [0, 0, 0, 0],
            "properties": {
                "datetime": "2026-01-01T00:00:00Z",
                "proj:code": "EPSG:4326",
            },
            "links": [],
            "assets": {},
        }
    )


if __name__ == "__main__":
    main()
