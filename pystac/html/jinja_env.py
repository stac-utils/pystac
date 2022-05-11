from functools import lru_cache
from itertools import islice


@lru_cache()
def get_jinja_env():  # type: ignore
    try:
        from jinja2 import Environment, PackageLoader, select_autoescape
    except ModuleNotFoundError:
        return None

    environment = Environment(
        loader=PackageLoader("pystac", "html"), autoescape=select_autoescape()
    )

    environment.filters["first"] = lambda x: islice(x, 1)
    environment.filters["is_nonempty_generator"] = lambda x: next(x, None) is not None

    return environment
