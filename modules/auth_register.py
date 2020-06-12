from app import app, bcrypt
from email_validator import validate_email
from itsdangerous import URLSafeTimedSerializer
from sanic_jwt import BaseEndpoint
from modules.database import DBHelper
from sanic import Blueprint, response
from app.email_sender import send_email

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

'''-----BLUEPRINTS-----'''

authBP = Blueprint('authBP')

@authBP.route('/reset-password', methods=['POST'])
async def reset_password_send_email(request):
    email = request.json.get('email', None)

    if validate_email(email):
        db_helper = DBHelper()
        user = await db_helper.async_select_db(app.client.energy_db.users, {"email" : email})
        if not user:
            raise PasswordResetFailed()

        token = ts.dumps(email, salt='recover-key')
        url = request.app.url_for('authBP.reset_password', token=token)
        url = app.config.HOST_NAME + url
        await send_email(email, "Восстановление пароля CK Energy", url)
        return response.json({'hit': 0})
    else:
        return response.json({'hit': 1})

@authBP.route('/reset-password-with-token', methods=['POST'])
async def reset_password(request):
    token = request.json['token']
    password = bcrypt.generate_password_hash(request.json['password'])

    try:
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except:
        raise RegistrationFailed()

    db_helper = DBHelper()
    await db_helper.update_row(app.client.energy_db.users, {"email" : email}, { "$set": {"password": password} })
    
    return response.json({'hit': 0})

@authBP.route('/approve-mail', methods=['POST'])
async def approve_email(request):
    try:
        email = ts.loads(request.json['token'], salt="approve-email-key", max_age=86400)
    except:
        raise RegistrationFailed()
    
    db_helper = DBHelper()
    await db_helper.update_row(app.client.energy_db.users, {"email" : email}, { "$set": { "isapprove": True } })

    return response.json({'hit': 0})

'''-------------'''

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
                raise RegistrationFailed("Пользователь с данной электронной почтой уже зарегистрирован")
            else:
                db_user = await db_helper.insert_db(app.client.energy_db.users, new_user)

            if db_user:
                try:
                    token = ts.dumps(email, salt='approve-email-key')
                    url = request.app.url_for('authBP.approve_email', token=token)
                    url = app.config.HOST_NAME + url
                    await send_email(email, "Подтверждение регистрации CK Energy", url)
                except:
                    await db_helper.delete_row(app.client.energy_db.users, {"_id" : db_user.inserted_id})
                    raise RegistrationFailed("Не удалось отправить письмо с подтверждением")

                response = self.responses.get_token_response(
                    request,
                    None,
                    None,
                    refresh_token=None,
                    config=self.config
                )
        else:
            raise RegistrationFailed("Неверный формат почты")

        return response

    @staticmethod
    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        pass

    @staticmethod
    def retrieve_refresh_token(request, user_id, *args, **kwargs):
        return "1234"

    @staticmethod
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
