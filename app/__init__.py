from sanic import Sanic
from sanic_cors import CORS
from sanic_jwt import Initialize

from simple_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer

from .mongo_blueprint import mongoBP
from modules.Register import Register
from modules.Auth import (
    Auth, 
    ResetPassword, 
    ResetPasswordWithToken, 
    ApproveEmail
)

from .models import User

app = Sanic(__name__)

app.config.SECRET_KEY='LOL'
app.config.SERVER_NAME='http://185.22.63.196:8888'
app.config.CORP_EMAIL='leonid_kit@mail.ru'
app.ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
app.bcrypt = Bcrypt(app)

app.blueprint(mongoBP)

my_views = (
    ('/register', Register),
    ('/reset-password', ResetPassword),
    ('/reset-password-with-token', ResetPasswordWithToken),
    ('/approve-email', ApproveEmail)
)

Initialize(
    app, 
    authenticate=Auth.authenticate, 
    retrieve_user=User.retrieve_user,
    class_views=my_views,
    refresh_token_enabled=True,
    store_refresh_token=Auth.store_refresh_token,
    retrieve_refresh_token=Auth.retrieve_refresh_token,
    add_scopes_to_payload=Auth.my_scope_extender,
    secret=app.config.SECRET_KEY,
    url_prefix='/api'
)
CORS(app, automatic_options=True)

from . import routes
