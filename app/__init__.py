from sanic import Sanic
from sanic.response import text, json
from sanic_cors import CORS
from sanic_jwt import Initialize, protected, exceptions

from datetime import datetime
from simple_bcrypt import Bcrypt

from .mongo_blueprint import mongoBP
from .exception import RegistrationFailed
from modules.database import DBHelper

app = Sanic(__name__)
app.config.SECRET_KEY='LOL'
app.config.HOST_NAME='http://localhost:8888'

bcrypt = Bcrypt(app)
app.blueprint(mongoBP)

from modules.auth_register import Register, authBP
app.blueprint(authBP)

my_views = (
    ('/register', Register),
)

Initialize(
    app, 
    authenticate=Register.authenticate, 
    class_views=my_views,
    refresh_token_enabled=True,
    store_refresh_token=Register.store_refresh_token,
    retrieve_refresh_token=Register.retrieve_refresh_token,
    secret=app.config.SECRET_KEY
)
CORS(app, automatic_options=True)

from . import routes