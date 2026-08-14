from tools.validate_repository_minimal import main


def test_repository_surface_is_minimal() -> None:
    assert main() == 0
