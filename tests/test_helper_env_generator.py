from settings import EpicSettings
from env_generator import generate_env_example_merged


def test_env_generator(tmp_path):
    env_text, output_file = generate_env_example_merged([EpicSettings], output_dir=tmp_path)

    assert output_file == tmp_path / ".env.example"
    assert output_file.read_text(encoding="utf-8") == env_text
    assert "EPIC_EMAIL=" in env_text
