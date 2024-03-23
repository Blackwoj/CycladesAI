from pathlib import Path


class AppSection:

    game_dir: Path = Path(__file__).resolve().parent.parent.parent
    assert_dir: Path = game_dir / 'assets'
    bid_icon_dir: Path = assert_dir / "bid_points"
    background_dir: Path = assert_dir / "backgrounds"
    nav_bar: Path = assert_dir / "nav_bar"
    players_icons: Path = assert_dir / "players_icons"

    players_names: list[str] = ["p1", "p2", "p3", "p4", "p5"]
    heros_names: list[str] = ["ares", "atena", "posejdon", "zeus"]
