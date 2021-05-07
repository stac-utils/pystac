import json
from pystac.validation import validate_dict

with open('test_validation/test_data/1rc1/extended-item.json') as f:
    js = json.load(f)
validate_dict(js)