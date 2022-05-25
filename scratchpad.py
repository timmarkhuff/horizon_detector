# 0.png,0.123432,0.923432
# 1.png,0.26734,0.723432
# 2.png,0.2343,0.35435

import os

dir = 'training_data/05.13.2022.18.40.13' #input('Enter the directory that contains the training data')
file_name = 'labels.txt'
full_filepath = f'{dir}/{file_name}'
label_dict = {}

# check if labels.txt exists. if not, create it
if os.path.exists(full_filepath):
  pass
else:
  with open(full_filepath, 'w') as f:
    pass

# check if the label file has a row for each image, if not, create one
items = os.listdir(dir) 
for item in items:
    if item[-4:] == ".png":
        if item not in label_dict:
          label_dict[item] = [None, None]

# read the file
with open(full_filepath, encoding='utf-8-sig') as f:
    lines = f.readlines()

# clean up the data and add items to dictionary
for line in lines:
  line = line.replace("\n","") # remove line breaks
  split = line.split(",")
  label_dict[split[0]] = (split[1], split[2])

# make some changes...
label_dict['187.png'] = (.23432,.999999)

# save changes
with open(full_filepath, 'w') as f:
  for key, value in label_dict.items():
    f.write(f"{key},{value[0]},{value[1]}\n")