from pathlib import Path


class AppSection:

    game_dir: Path = Path(__file__).resolve().parent.parent.parent
    assert_dir: Path = game_dir / 'assets'
    background_dir: Path = assert_dir / "backgrounds"
    nav_bar: Path = assert_dir / "nav_bar"
