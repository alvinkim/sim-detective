import pytest

from simdet.config import load_config
from simdet.scenario import generate as g


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture(scope="session")
def scenario_set(cfg, tmp_path_factory):
    """The full 60-scenario set, generated once into a temporary directory."""
    root = tmp_path_factory.mktemp("scenarios")
    result = g.generate(cfg, 60, 0)
    g.save(result, root)
    privates = [s["private"] for s in result["scenarios"]]
    publics = {s["public"]["id"]: s["public"] for s in result["scenarios"]}
    return {"root": root, "public_dir": root / "public", "private_dir": root / "private",
            "privates": privates, "publics": publics, "result": result}
