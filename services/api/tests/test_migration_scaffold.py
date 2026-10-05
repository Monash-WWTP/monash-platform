from pathlib import Path
from shutil import copytree

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_can_generate_next_revision(tmp_path):
    source = Path(__file__).resolve().parents[1] / "alembic"
    target = tmp_path / "alembic"
    copytree(source, target)
    config = Config()
    config.set_main_option("script_location", str(target))
    revision = ScriptDirectory.from_config(config).generate_revision(
        "test_next", "next schema"
    )
    assert Path(revision.path).exists()
    assert revision.down_revision == "d57267a1d090"
