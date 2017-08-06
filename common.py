import json


def read_from_json(fname):
    with open(fname) as fobj:
        return json.load(fobj)


def write_to_json(data, fname):
    with open(fname, 'w') as fobj:
        json.dump(data, fobj, indent=2, sort_keys=True)
