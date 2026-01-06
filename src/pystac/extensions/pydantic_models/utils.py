from typing import Any, override

from pydantic import BaseModel, RootModel


class FieldsModel(BaseModel):
    _frozen: bool = False

    def __init__(self, frozen: bool = False, **data: Any):
        super().__init__(**data)
        if frozen:
            model = self
            model._frozen = True
            for name, field in model.__class__.model_fields.items():
                field.frozen = frozen
                if isinstance(getattr(self, name), RootModel):
                    for model in getattr(self, name).root:
                        for name, field in model.__class__.model_fields.items():
                            field.frozen = frozen
                elif isinstance(getattr(self, name), BaseModel):
                    model = getattr(self, name)
                    for name, field in model.__class__.model_fields.items():
                        field.frozen = frozen

    @override
    def __repr__(self) -> str:
        if getattr(self, "_frozen"):
            return f"FrozenView {super().__repr__()}"
        return super().__repr__()
