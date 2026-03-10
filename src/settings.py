from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    data_dir: Path = Path("/data")
    results_file: Path | None = None
    feedback_candidate_file: Path | None = None

    @property
    def candidates_file(self) -> Path:
        return self.data_dir / "candidates.json"

    @property
    def output_results_file(self) -> Path:
        return self.results_file if self.results_file is not None else self.data_dir / "results.json"

    @property
    def feedback_file(self) -> Path:
        return self.data_dir / "feedback_file.json"


settings = Settings()
