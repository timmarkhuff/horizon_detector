from old.config import Settings

run = True
recording = False

path = 'settings.txt'
settings_dict = {
    'ail_kp': 0.015,
    'elev_kp': 0.0375,
    'easy_mode_limit_roll': 30,
    'easy_mode_limit_pitch': 10,
    'max_deflection': .4,
    'servos_reversed': 0,
    'source': '0',
    'fps': 30,
    'inference_resolution': '(100,100)',
    'resolution': '(640,480)',
    'acceptable_variance': 1.3,
    'exclusion_thresh': 4,       
    # FOV constant for Raspberry Pi Camera v2
    # for more info: https://www.raspberrypi.com/documentation/accessories/camera.html
    'fov': 48.8       
}

dtype_dict = {
    'ail_kp': float,
    'elev_kp': float,
    'easy_mode_limit_roll': int,
    'easy_mode_limit_pitch': int,
    'max_deflection': float,
    'servos_reversed': int,
    'source': str,
    'fps': int,
    'inference_resolution': eval,
    'resolution': eval,
    'acceptable_variance': float,
    'exclusion_thresh': float,
    'fov': float
}

settings = Settings(path, settings_dict, dtype_dict)
