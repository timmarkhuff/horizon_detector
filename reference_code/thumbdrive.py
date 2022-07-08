import os

file_path = '/media/pi/329A-3084'

if not os.path.exists(file_path):
    print('Does not exist.')
else:
    print('Already exists.')


