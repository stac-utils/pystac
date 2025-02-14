from .extension import Extension


class ProjectionExtension(Extension):
    code: str | None

    @classmethod
    def get_name(cls) -> str:
        return "projection"

    @classmethod
    def get_slug(cls) -> str:
        return "proj"

    @classmethod
    def get_default_version(cls) -> str:
        return "2.0.0"
