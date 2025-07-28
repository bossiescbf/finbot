from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseConfig(BaseModel):
    """Настройки базы данных"""
    host: str
    port: int
    name: str
    user: str
    password: str
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class BotConfig(BaseModel):
    """Настройки бота"""
    token: str
    admin_ids: list[int]

class Settings(BaseSettings):
    """Основной класс настроек приложения"""
    
    # Токен бота (обязательный)
    bot_token: str
    
    # ID администраторов
    admin_ids: str
    
    # Настройки базы данных
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    # Redis
    redis_url: str
    
    # Общие настройки
    debug: bool = False
    log_level: str = "INFO"
    
    # Webhook настройки
    use_webhook: bool = True
    domain: str
    webhook_path: str
    webhook_secret: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=self.db_host,
            port=self.db_port,
            name=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    @property
    def bot(self) -> BotConfig:
        admin_list = [int(id.strip()) for id in self.admin_ids.split(",") if id.strip().isdigit()]
        return BotConfig(
            token=self.bot_token,
            admin_ids=admin_list
        )

# Создание экземпляра настроек
settings = Settings()