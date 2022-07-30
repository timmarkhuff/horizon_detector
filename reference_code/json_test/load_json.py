import json

# Opening JSON file
with open('test_json.txt') as json_file:
    datadict = json.load(json_file)

print(datadict['metadata']['fps'])