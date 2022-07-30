import json

datadict = {}
metadata = {}

# meta data
datadict['metadata'] = metadata
metadata['fps'] = 30
metadata['datetime'] = '6/5/2022'


# frame data
for n in range(10):
    frame_details_dict = {}
    frame_details_dict['horizon'] = .344332432
    frame_details_dict['offset'] = .234832
    datadict[n] = frame_details_dict

print(datadict)

# save the json file
with open('test_json.txt', 'w') as convert_file: 
    convert_file.write(json.dumps(datadict))