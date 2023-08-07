from abc import ABC
import yaml
from typing import Any

class Message(ABC):
    def __init__(self, data=None):
        """Allows dictionaries to be handled like objects with dot notation.
        For example, you can write config.video.fps instead of config['video']['fps']

        Inspired by ROS message: http://wiki.ros.org/msg
        """
        if data is None:
            data = {}
        self.data = data
    
    def __getattr__(self, key) -> Any:
        value = self.data[key]
        if isinstance(value, dict):
            return Message(value)
        else:
            return value

    def __setattr__(self, key, value) -> None:
        if key == "data":
            super().__setattr__(key, value)
        else:
            keys = key.split('.')
            current_dict = self.data
            for k in keys[:-1]:
                current_dict = current_dict.setdefault(k, {})
            current_dict[keys[-1]] = value

    def __repr__(self) -> str:
        return str(self.data)
    
    def __str__(self) -> str:
        str_repr = '-' * 20 + '\n'
        str_repr += type(self).__name__ + '\n'
        str_repr += yaml.dump(self.data, indent=2)
        return str_repr
    
class ParsedPacket(Message):
    def __init__(self):
        self.data = {
                'sticks': {
                    'ail': 0,
                    'ele': 0,
                    'thr': -1,
                    'rud': 0,
                },
                'trim': {
                    'ail': 0,
                    'ele': 0,
                    'rud': 0,
                },
                'switches': {
                    'rec': 0,
                    'auto': 0,
                }
            }

class Attitude(Message):
    def __init__(self):
        self.data = {
            'pitch': 0,
            'roll': 0,
            'yaw': 0,
            }
        
class Horizon(Message):
    def __init__(self):
        self.data = {
            'attitude': Attitude().data,
            'confidence': 0,
        }