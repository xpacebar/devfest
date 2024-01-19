from flask import Flask
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    """Application factory"""
    from pkg.models import db
    from pkg import config

    app=Flask(__name__,instance_relative_config=True)

    app.config.from_pyfile('config.py')
    app.config.from_object(config.TestConfig)
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app,db)
    return app

app = create_app()
from pkg import admin_routes, user_routes