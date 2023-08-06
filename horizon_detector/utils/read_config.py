import yaml

SEPARATOR = '/'

def read_and_flatten_yaml(path: str) -> dict:
    """Reads a yaml file with nested configurations and returns
    a flat dictionary of configurations.

    Rationale: this project has a nested structure of configurations to provide better
    organization and semantic relationship. However, since the program accesses these 
    configurations rapidly and continously in the main loop, we flatten the configuration 
    for faster lookup. 
    
    It also saves a few characters when referencing these configurations in code, e.g.
    you can write:
    config['receiver/channels/primary/ele']
    ...instead of...
    config['receiver']['channels']['primary']['ele']
    """
    with open(path, "r") as file:
        config = yaml.safe_load(file)

    return _flatten_config(config)

def _flatten_config(config: dict, parent_key: str = "") -> dict:
    flattened_config = {}
    for key, value in config.items():
        new_key = f"{parent_key}{SEPARATOR}{key}" if parent_key else key
        if isinstance(value, dict):
            flattened_config.update(_flatten_config(value, new_key))
        else:
            flattened_config[new_key] = value
    return flattened_config
