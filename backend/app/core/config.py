from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    linode_access_key: str
    linode_secret_key: str
    linode_bucket: str
    linode_endpoint: str
    secret_key: str
    bootstrap_admin_email: str = ""
    max_upload_mb: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
