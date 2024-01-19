class Config:
    APP_NAME="Devfest"

class LiveConfig(Config):
    DBNAME = "live"
    DBPWD= "live1234"

class TestConfig(Config):
    DBNAME = "test"
    DBPWD = "test1234"