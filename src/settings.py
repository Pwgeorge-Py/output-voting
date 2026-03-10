from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    data_dir: Path = Path("/data")

    @property
    def candidates_file(self) -> Path:
        return self.data_dir / "candidates.json"

    @property
    def results_file(self) -> Path:
        return self.data_dir / "results.json"


settings = Settings()
