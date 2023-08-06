from horizon_detector.utils import read_and_flatten_yaml

class TestUtils:
    def test_read_and_flatten_yaml(self):
        path = 'configurations.yaml'
        config = read_and_flatten_yaml(path)
        
        # Check that the keys were flattened correctly and contains '/'
        for key in config.keys():
            assert '/' in key




              