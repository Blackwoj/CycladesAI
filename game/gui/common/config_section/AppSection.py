from pathlib import Path


class AppSection:

    game_dir: Path = Path(__file__).resolve().parent.parent.parent
    assert_dir: Path = game_dir / 'assets'
    bid_icon_dir: Path = assert_dir / "bid_points"
    background_dir: Path = assert_dir / "backgrounds"
    heros_plates: Path = assert_dir / "heros_boards"
    nav_bar: Path = assert_dir / "nav_bar"
    players_icons: Path = assert_dir / "players_icons"

    boards_path: Path = assert_dir / "board" / "DEV"
    boards_items: Path = assert_dir / "boards_items"
    building_icons: Path = boards_items / "buildings"

    players_names: list[str] = ["p1", "p2", "p3", "p4", "p5"]
    heros_names: list[str] = ["ares", "atena", "posejdon", "zeus"]

    ai_player: list[str] = ["p5"]
    train_ai_player: list[str] = ["p1", "p2", "p3", "p4"]
