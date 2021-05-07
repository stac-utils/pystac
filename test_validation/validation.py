import json
from pystac.validation import validate_dict

with open('../test_validation/test_data/1rc2/simple-item.json') as f:
    js = json.load(f)
result = validate_dict(js)
print(result)