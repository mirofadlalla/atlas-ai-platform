from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    postgres_user : str = "postgres"
    postgres_pass : str = "1234"
    postgres_host : str = "localhost"
    postgres_port : int = 5432
    postgres_db : str =  ""
    hf_api : str = ""
    api_secret_key : str = ""


    class Config:
        env_file = '.env'
        extra = "ignore"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_pass}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
settings = Settings()
