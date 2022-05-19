import json


def json_reader(file_name: str):
    with open(file_name, 'r') as f:
        try:
            return json.loads(f.read())
        except Exception as e:
            return e
            