# TODO refactor, and probably deprecate get_opt

import datetime
import os.path
import posixpath
import urllib.parse
from pathlib import Path
from typing import TypeVar
from urllib.parse import ParseResult

import dateutil.parser

T = TypeVar("T")


def is_absolute_href(href: str) -> bool:
    parsed = safe_urlparse(href)
    return parsed.scheme not in ["", "file"] or os.path.isabs(parsed.path)


def safe_urlparse(href: str) -> ParseResult:
    parsed = urllib.parse.urlparse(href)
    if parsed.scheme != "" and (
        href.lower().startswith(f"{parsed.scheme}:\\")
        or (
            href.lower().startswith(f"{parsed.scheme}:/")
            and not href.lower().startswith(f"{parsed.scheme}://")
        )
    ):
        return ParseResult(
            scheme="",
            netloc="",
            # We use this more complicated formulation because parsed.scheme
            # converts to lower-case
            path=f"{href[: len(parsed.scheme)]}:{parsed.path}",
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
        )

    # Windows drives sometimes get parsed as the netloc and sometimes
    # as part of the parsed.path.
    if parsed.scheme == "file" and os.name == "nt":
        if parsed.netloc:
            path = f"{parsed.netloc}{parsed.path}"
        elif parsed.path.startswith("/") and ":" in parsed.path:
            path = parsed.path[1:]
        else:
            path = parsed.path

        return ParseResult(
            scheme=parsed.scheme,
            netloc="",
            path=path,
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
        )
    else:
        return parsed


def make_absolute_href(
    source_href: str, start_href: str | None = None, start_is_dir: bool = False
) -> str:
    if start_href is None:
        start_href = os.getcwd()
        start_is_dir = True

    source_href = make_posix_style(source_href)
    start_href = make_posix_style(start_href)

    parsed_start = safe_urlparse(start_href)
    parsed_source = safe_urlparse(source_href)

    if parsed_source.scheme not in ["", "file"] or parsed_start.scheme not in [
        "",
        "file",
    ]:
        return _make_absolute_href_url(parsed_source, parsed_start, start_is_dir)
    else:
        return _make_absolute_href_path(parsed_source, parsed_start, start_is_dir)


def _make_absolute_href_path(
    parsed_source: ParseResult,
    parsed_start: ParseResult,
    start_is_dir: bool = False,
) -> str:
    # If the source is already absolute, just return it
    if os.path.isabs(parsed_source.path):
        return urllib.parse.urlunparse(parsed_source)

    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else os.path.dirname(parsed_start.path)
    )

    # Join the start directory to the relative path and find the absolute path
    abs_path = make_posix_style(
        os.path.abspath(os.path.join(start_dir, parsed_source.path))
    )

    # Account for the normalization of abspath for
    # things like /vsitar// prefixes by replacing the
    # original start_dir text when abspath modifies the start_dir.
    if not start_dir == make_posix_style(os.path.abspath(start_dir)):
        abs_path = abs_path.replace(
            make_posix_style(os.path.abspath(start_dir)), start_dir
        )

    if parsed_source.scheme or parsed_start.scheme:
        abs_path = f"file://{abs_path}"

    return abs_path


def _make_absolute_href_url(
    parsed_source: ParseResult,
    parsed_start: ParseResult,
    start_is_dir: bool = False,
) -> str:
    # If the source is already absolute, just return it
    if parsed_source.scheme != "":
        return urllib.parse.urlunparse(parsed_source)

    # If the start path is not a directory, get the parent directory
    if start_is_dir:
        start_dir = parsed_start.path
    else:
        # Ensure the directory has a trailing slash so urljoin works properly
        start_dir = parsed_start.path.rsplit("/", 1)[0] + "/"

    # Join the start directory to the relative path and find the absolute path
    abs_path = urllib.parse.urljoin(start_dir, parsed_source.path)
    abs_path = abs_path.replace("\\", "/")

    return urllib.parse.urlunparse(
        (
            parsed_start.scheme,
            parsed_start.netloc,
            abs_path,
            parsed_source.params,
            parsed_source.query,
            parsed_source.fragment,
        )
    )


def make_posix_style(href: str | Path) -> str:
    _href = str(os.fspath(href))
    return _href.replace("\\\\", "/").replace("\\", "/")


def make_relative_href(
    source_href: str, start_href: str, start_is_dir: bool = False
) -> str:
    source_href = make_posix_style(source_href)
    start_href = make_posix_style(start_href)

    parsed_source = safe_urlparse(source_href)
    parsed_start = safe_urlparse(start_href)
    if not (
        parsed_source.scheme == parsed_start.scheme
        and parsed_source.netloc == parsed_start.netloc
    ):
        return source_href

    if parsed_start.scheme in ["", "file"]:
        return _make_relative_href_path(parsed_source, parsed_start, start_is_dir)
    else:
        return _make_relative_href_url(parsed_source, parsed_start, start_is_dir)


def _make_relative_href_path(
    parsed_source: ParseResult,
    parsed_start: ParseResult,
    start_is_dir: bool = False,
) -> str:
    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else os.path.dirname(parsed_start.path)
    )

    # Strip the leading slashes from both paths
    start_dir = start_dir.lstrip("/")
    source_path = parsed_source.path.lstrip("/")

    # posixpath doesn't play well with windows drive letters, so we have to use
    # the os-specific path library for the relpath function. This means we can
    # only handle windows paths on windows machines.
    relpath = make_posix_style(os.path.relpath(source_path, start_dir))

    # Ensure we retain a trailing slash from the original source path
    if parsed_source.path.endswith("/"):
        relpath += "/"

    if relpath != "./" and not relpath.startswith("../"):
        relpath = "./" + relpath

    return relpath


def _make_relative_href_url(
    parsed_source: ParseResult,
    parsed_start: ParseResult,
    start_is_dir: bool = False,
) -> str:
    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else os.path.dirname(parsed_start.path)
    )

    # Strip the leading slashes from both paths
    start_dir = start_dir.lstrip("/")
    source_path = parsed_source.path.lstrip("/")

    # Get the relative path
    rel_url = posixpath.relpath(source_path, start_dir)

    # Ensure we retain a trailing slash from the original source path
    if parsed_source.path.endswith("/"):
        rel_url += "/"

    # Prepend the "./", if necessary
    if rel_url != "./" and not rel_url.startswith("../"):
        rel_url = "./" + rel_url

    return rel_url


def datetime_to_str(dt: datetime.datetime, timespec: str = "auto") -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)

    timestamp = dt.isoformat(timespec=timespec)
    zulu = "+00:00"
    if timestamp.endswith(zulu):
        timestamp = f"{timestamp[: -len(zulu)]}Z"

    return timestamp


def str_to_datetime(s: str) -> datetime.datetime:
    return dateutil.parser.isoparse(s)


def get_opt(option: T | None) -> T:
    if option is None:
        raise ValueError("Cannot get value from None")
    return option
