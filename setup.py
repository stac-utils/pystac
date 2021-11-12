import os
from setuptools import setup, find_packages
from glob import glob

from os.path import basename, splitext

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md")) as readme_file:
    readme = readme_file.read()

setup(
    name="pystac",
    description=(
        "Python library for working with Spatiotemporal Asset Catalog (STAC)."
    ),
    long_description=readme,
    long_description_content_type="text/markdown",
    author="stac-utils",
    author_email="stac@radiant.earth",
    url="https://github.com/stac-utils/pystac",
    packages=find_packages(exclude=["tests*"]),
    package_data={"": ["py.typed"]},
    py_modules=[splitext(basename(path))[0] for path in glob("pystac/*.py")],
    python_requires=">=3.7",
    install_requires=[
        "python-dateutil>=2.7.0",
        'typing_extensions >= 3.7; python_version < "3.8"',
    ],
    extras_require={"validation": ["jsonschema>=3.0"], "orjson": ["orjson>=3.5"]},
    license="Apache Software License 2.0",
    license_files=["LICENSE"],
    zip_safe=False,
    keywords=["pystac", "imagery", "raster", "catalog", "STAC"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    project_urls={
        "Tracker": "https://github.com/stac-utils/pystac/issues",
        "Documentation": "https://pystac.readthedocs.io/en/latest/",
        "GitHub Discussions": (
            "https://github.com/radiantearth/stac-spec/discussions/categories/pystac"
        ),
    },
    test_suite="tests",
)
