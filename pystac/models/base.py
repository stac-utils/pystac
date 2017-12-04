import json


class STACObject(object):
    @property
    def dict(self):
        raise NotImplementedError('Dict Serialization Not Implemented')

    @property
    def json(self) -> str:
        return json.dumps(self.dict)
