from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "MONEQ DEAL FINDER API"
    app_env: str = "development"
    cors_origins: str = "*"

    naver_client_id: str = ""
    naver_client_secret: str = ""
    gemini_api_key: str = ""

    daangn_partner_api_key: str = ""
    daangn_partner_endpoint: str = ""
    bunjang_partner_api_key: str = ""
    bunjang_partner_endpoint: str = ""

    database_path: str = "./moneq_deals.db"
    cache_ttl_seconds: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
