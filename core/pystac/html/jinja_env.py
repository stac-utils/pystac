from functools import lru_cache


@lru_cache
def get_jinja_env():  # type: ignore
    try:
        from jinja2 import Environment, PackageLoader, select_autoescape
    except ModuleNotFoundError:
        return None

    environment = Environment(
        loader=PackageLoader("pystac", "html"), autoescape=select_autoescape()
    )

    return environment
