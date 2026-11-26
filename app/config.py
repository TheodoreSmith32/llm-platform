from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gateway_api_keys: str = "sk-internal-dev"
    audit_log_path: str = "audit.jsonl"

    s3_endpoint_url: str | None = None
    s3_bucket: str = "llm-raw-uploads"
    file_ttl_days: int = 7

    local_model: str = "ollama/llama3"
    local_api_base: str = "http://localhost:11434"

    @property
    def api_keys(self) -> set[str]:
        return {k.strip() for k in self.gateway_api_keys.split(",") if k.strip()}


settings = Settings()
