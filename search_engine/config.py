import tomllib
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"

def load(config_path: Path = _DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    config["database"]["path"] = str(Path(config["database"]["path"]).expanduser())
    
    config["indexer"]["root"] = str(Path(config["indexer"]["root"]).expanduser())

    return config
