import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class BaseSettings(BaseSettings):
    DATABASE_URL: str

    model_config = {"env_file":".env", "extra": "ignore",}


class DevelopmentSettings(BaseSettings):
    pass

class TestingSettings(BaseSettings):
    pass


class ProductionSettings(BaseSettings):
    pass



@lru_cache
def get_settings():
    config_cls_dict = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings
    }
    config_name = os.getenv("FASTAPI_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()

settings = get_settings()
