from sanic import Sanic
from sanic.response import text, json
from sanic_cors import CORS

from datetime import datetime

from sanic_jwt import Initialize, BaseEndpoint, protected, exceptions
from itsdangerous import URLSafeTimedSerializer

from simple_bcrypt import Bcrypt
from email_validator import validate_email

from .mongo_blueprint import mongo_bp
from .exception import RegistrationFailed
from .email_sender import send_email

class DBHelper():
    async def insert_db(self, collection, data):
        user = await collection.insert_one(data)
        return user.inserted_id
    async def async_select_db(self, collection, data):
        user = await collection.find_one(data)
        return user
    async def update_row(self, collection, row_ident, data):
        return await collection.update_one(row_ident, data)

class Register(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        request_json = request.json

        email = request_json['email']
        email_valid = validate_email(email)

        if email_valid:
            new_user = {
                "email": request_json['email'],
                "user_name": request_json['user_name'],
                "phone": request_json['phone'],
                "company_name": request_json['company_name'],
                "password": bcrypt.generate_password_hash(request_json['password']).decode('utf-8'),
                "isapprove": False,
                "register_date": datetime.now(),
                "scopes": ['user']
            }
            db_helper = DBHelper()
            db_user = await db_helper.async_select_db(app.client.energy_db.users, {"email" : request_json['email']})
            
            if db_user:
                raise RegistrationFailed("The user is already in the database")
            else:
                db_user = await db_helper.insert_db(app.client.energy_db.users, new_user)

            if db_user:
                token = ts.dumps(email, salt='approve-email-key')
                url = app.url_for('approve_email', token=token)
                url = 'http://localhost:8888' + url
                await send_email(email, "Подтверждение регистрации CK Energy", url)

                # user = await request.app.auth.authenticate(request, *args, **kwargs)
                # access_token, output = await self.responses.get_access_token_output(
                #     request,
                #     user,
                #     self.config,
                #     self.instance
                # )

                # refresh_token = await self.instance.auth.generate_refresh_token(request, user)
                # output.update({
                #     self.config.refresh_token_name: refresh_token
                # })

                response = self.responses.get_token_response(
                    request,
                    None,
                    None,
                    refresh_token=None,
                    config=self.config
                )
        else:
            raise RegistrationFailed("Invalid mail format")

        return response

async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
    pass

def retrieve_refresh_token(request, user_id, *args, **kwargs):
    return "1234"

async def authenticate(request):
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    if not email or not password:
        raise exceptions.AuthenticationFailed(403)
    
    db_helper = DBHelper()
    user = await db_helper.async_select_db(app.client.energy_db.users, {"email" : email})

    if user.get('isapprove') == False:
        raise exceptions.AuthenticationFailed(403)

    if user is None:
        raise exceptions.AuthenticationFailed(403)

    if not bcrypt.check_password_hash(user.get('password', None), password):
        raise exceptions.AuthenticationFailed(403)

    return user


my_views = (
    ('/register', Register),
)

app = Sanic(__name__)
app.config.SECRET_KEY='LOL'

bcrypt = Bcrypt(app)
app.blueprint(mongo_bp)

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

Initialize(
    app, 
    authenticate=authenticate, 
    class_views=my_views,
    refresh_token_enabled=True,
    store_refresh_token=store_refresh_token,
    retrieve_refresh_token=retrieve_refresh_token
)
CORS(app, automatic_options=True)

from . import routes