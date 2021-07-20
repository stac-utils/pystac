from jinja2 import Environment, PackageLoader, select_autoescape  # type: ignore

jinja_env = Environment(
    loader=PackageLoader("pystac", "html"), autoescape=select_autoescape()
)
