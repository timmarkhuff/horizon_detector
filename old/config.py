import os

class Settings:
    def __init__(self, path: str, settings_dict: dict, dtype_dict: dict):
        self.path = path
        self.settings_dict = settings_dict
        self.dtype_dict = dtype_dict

        if not os.path.exists(self.path):
            self.write()

    def read(self):
        with open(self.path, 'r') as f:
            lines = f.readlines()

        temp_dict = {}
        for line in lines:
            line = line.strip()
            # skip comments
            if line[0] == '#':
                continue

            if ':' not in line:
                continue

            line_split = line.split(':', 1)
            key = line_split[0]
            value = line_split[1]

            if key not in self.settings_dict.keys():
                continue
            
            # convert to the proper data type
            dtype = self.dtype_dict[key]
            value = dtype(value)

            # add to the dict
            temp_dict[key] = value

        # check if the number of read settings equals the number of settings 
        # that should be in the dict
        if len(temp_dict.keys()) == len(self.settings_dict.keys()):
            ret = True
            self.settings_dict = temp_dict
            self.print_values()
        else:
            ret = False

        return ret

    def get_value(self, key):
        return self.settings_dict[key]

    def update_value(self, key, value):
        """
        for updating a value during runtime
        """
        self.settings_dict[key] = value

    def write(self):
        """
        writes self.settings_dict as a txt file
        """
        str_to_write = '# Settings for the Flight Controller'
        for key, value in self.settings_dict.items():
            line_to_add = f'\n{key}:{value}'
            str_to_write += line_to_add

        with open(self.path, 'w') as f:
            f.write(str_to_write)

    def print_values(self):
        """
        prints all values of self.settings_dict
        """
        print('-----SETTINGS-----')
        for key, value in self.settings_dict.items():
            print(f'{key}: {value} {type(value)}')
        print('------------------')

if __name__ == '__main__':
    path = 'test_settings.txt'
    settings_dict = {
        'ail_trim': 0,
        'elev_trim': 0,
        'ail_kp': .001,
        'elev_kp': .0025,
        'source': '0',
        'fps': 30,
        'inf_res': '(100,100)',
        'resolution': '(640,480)',
        'acceptable_variance': 1.3
    }

    dtype_dict = {
        'ail_trim': float,
        'elev_trim': float,
        'ail_kp': float,
        'elev_kp': float,
        'source': str,
        'fps': int,
        'inf_res': eval,
        'resolution': eval,
        'acceptable_variance': float
    }

    settings = Settings(path, settings_dict, dtype_dict)
    ret = settings.read()
    print(f'ret: {ret}')
    if ret: 
        settings.print_values()

        print('----------')
        print('Getting a value...')
        ail_trim = settings.get_value('ail_trim')
        print(f'ail_trim: {ail_trim}')

        print('----------')
        print('Updating a value...')
        settings.update_value('ail_trim', .09999)

        print('----------')
        print('Getting value again...')
        ail_trim = settings.get_value('ail_trim')
        print(f'ail_trim: {ail_trim}')

        print('----------')
        print('Writing values...')
        settings.write()