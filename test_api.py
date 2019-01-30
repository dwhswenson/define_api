import pytest
import importlib

# select the file you want to use, or change to the file for your own API
API_FILE = "good_api.txt"
API_FILE = "bad_api.txt"
COMBO_ERROR = False

def test_api():
    def import_object(import_path):
        path = import_path.split('.')
        current = importlib.import_module(path[0])
        for mod in path[1:]:
            current = getattr(current, mod)
        return current

    with open(API_FILE, mode='r') as api_file:
        tests = api_file.read().splitlines()

    errors = []
    for test in tests:
        try:
            obj = import_object(test)
        except AttributeError as e:
            if COMBO_ERROR:
                errors.append(test)
            else:
                raise e

    if errors:
        raise AssertionError("Some API entries failed: " + str(errors))

