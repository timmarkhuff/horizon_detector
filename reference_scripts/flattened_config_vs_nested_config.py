from flight_controller import read_and_flatten_yaml

path = "configurations.yaml"
config = read_and_flatten_yaml(path)
print(config)
