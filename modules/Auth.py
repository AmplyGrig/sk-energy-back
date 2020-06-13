from email_validator import validate_email
from modules.database import DBHelper
from sanic import Blueprint, response
from sanic.log import logger
from modules.email_sender import send_email
from sanic_jwt import BaseEndpoint, exceptions
from app.exception import PasswordResetFailed, RegistrationFailed

class Auth:
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
            logger.error('Неверный логин или пароль')
            raise exceptions.AuthenticationFailed('Неверный логин или пароль')
        
        db_helper = DBHelper()
        user = await db_helper.async_select_db(
            request.app.client.energy_db.users,
            {"email" : email}
        )

        if user is None:
            logger.error('Пользователя не существует')
            raise exceptions.AuthenticationFailed('Пользователя не с данной почтой существует')

        if user.get('is_approve') == False:
            logger.error('Аккаунт пользователя не подтвержден')
            raise exceptions.AuthenticationFailed('Аккаунт пользователя не подтвержден')

        if not request.app.bcrypt.check_password_hash(user.get('password', None), password):
            logger.error('Неверный логин или пароль')
            raise exceptions.AuthenticationFailed('Неверный логин или пароль')

        return { 'user_id' : str(user.get('_id')) }

class ResetPassword(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        email = request.json.get('email', None)

        try:
            validate_email(email)
        except:
            logger.error('Неверный формат почты')
            raise PasswordResetFailed('Неверный формат почты')

        db_helper = DBHelper()
        user = await db_helper.async_select_db(request.app.client.energy_db.users, {"email" : email})
        if not user:
            logger.error('Пользователя не существует')
            raise PasswordResetFailed('Пользователя не с данной почтой существует')

        token = request.app.ts.dumps(email, salt='recover-key')
        url = request.url_for('auth_bp.ResetPassword', token=token)
        await send_email(email, "Восстановление пароля CK Energy", url)

        return response.json({'hit': 0})

class ResetPasswordWithToken(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        token = request.json['token']
        password = request.app.bcrypt.generate_password_hash(request.json['password'])

        try:
            email = request.app.ts.loads(token, salt="recover-key", max_age=86400)
        except:
            logger.error('Время действия ссылки истекло')
            raise PasswordResetFailed('Время действия ссылки истекло')

        db_helper = DBHelper()
        await db_helper.update_row(
            request.app.client.energy_db.users, 
            {"email" : email}, 
            { "$set": {
                    "password": password
                } 
            }
        )
        
        return response.json({'hit': 0})

class ApproveEmail(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        db_helper = DBHelper()
        try:
            email = request.app.ts.loads(
                request.json['token'], 
                salt="approve-email-key",
                max_age=86400
            )
        except Exception as e:
            await db_helper.delete_row(request.app.client.energy_db.users, {"email" : email})
            logger.error('Время действия ссылки истекло')
            raise RegistrationFailed("Время действия ссылки истекло.")
        
        await db_helper.update_row(
            request.app.client.energy_db.users, 
            {"email" : email},
            { "$set": {
                    "is_approve": True 
                } 
            }
        )
        return response.json({'hit': 0})
