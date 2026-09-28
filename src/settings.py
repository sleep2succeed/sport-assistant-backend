from pathlib import Path

from pydantic import SecretStr, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property

class LlmConfig(BaseModel):
    API_KEY: SecretStr = SecretStr("EMPTY")
    BASE_URL: str = "http://base"
    RESPONSE_TIMEOUT: int = 60
    MODEL_NAME: str = "."
    TEMPERATURE: float = 0.1
    TOP_P: float = 0.5
    MAX_TOKENS: int = 10000
    ENABLE_THINKING: bool = False
    ADD_EXTRA_BODY: bool = True

class GoogleHealthConfig(BaseModel):
    CLIENT_SECRETS_FILE: Path = Path("client_secret.json")
    TOKEN_FILE: Path = Path("token.json")
    TIMEZONE: str = "Europe/Moscow"

class TokenizerConfig(BaseModel):
    TOKENIZER_PATH: Path = Path("backend/tokenizer_files/Qwen3_tokenizer")
    MAX_CONTEXT_TOKENS: int = 64_000

class ProxyConfig(BaseModel):
    PASSWORD: SecretStr = SecretStr("EMPTY")
    USERNAME: SecretStr = SecretStr("USER")
    IP_ADDRESS: str = "http://127.0.0.1:8080"

    @cached_property
    def url(self) -> str:
        user_name = self.USERNAME.get_secret_value()
        password = self.PASSWORD.get_secret_value()
        return f"socks5://{user_name}:{password}@{self.IP_ADDRESS}"

class PostgresqlConfig(BaseModel):
    PASSWORD: SecretStr = SecretStr("EMPTY")
    USERNAME: SecretStr = SecretStr("USER")
    HOST: str = "http://127.0.0.1"
    PORT: str = "8080"
    DB_NAME: str = "sport_assistant"

    @cached_property
    def url(self) -> str:
        user_name = self.USERNAME.get_secret_value()
        password = self.PASSWORD.get_secret_value()
        return f"postgresql://{user_name}:{password}@{self.IP_ADDRESS}"

class Settings(BaseSettings):
    tokenizer: TokenizerConfig = TokenizerConfig()
    llm: LlmConfig = LlmConfig()
    postgresql: PostgresqlConfig = PostgresqlConfig()
    proxy: ProxyConfig = ProxyConfig()
    google_health: GoogleHealthConfig = GoogleHealthConfig()

    @cached_property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @cached_property
    def migrations_dir(self) -> Path:
        return self.project_root / "migrations"

    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=".env"
    )


settings = Settings()