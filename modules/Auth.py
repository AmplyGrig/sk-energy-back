from email_validator import validate_email
from modules.database import DBHelper
from sanic import Blueprint, response
from sanic.log import logger
from modules.email_sender import send_email
from sanic_jwt import BaseEndpoint, exceptions
from app.exception import PasswordResetFailed, RegistrationFailed
from app.models import User

class Auth:
    @staticmethod
    async def my_scope_extender(user, *args, **kwargs):
        return user['role']

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
        
        user = User(request.app.client.energy_db.users)
        user = await user.get(email=email)
        
        if user is None:
            logger.error('Пользователя не существует')
            raise exceptions.AuthenticationFailed('Пользователя не с данной почтой существует')

        if user.get('is_approve') == False:
            logger.error('Аккаунт пользователя не подтвержден')
            raise exceptions.AuthenticationFailed('Аккаунт пользователя не подтвержден')

        if not request.app.bcrypt.check_password_hash(user.get('password', None), password):
            logger.error('Неверный логин или пароль')
            raise exceptions.AuthenticationFailed('Неверный логин или пароль')

        return { 'user_id' : str(user.get('_id')), 'role': user.get('role') }

class ResetPassword(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        email = request.json.get('email', None)

        try:
            validate_email(email)
        except:
            logger.error('Неверный формат почты')
            raise PasswordResetFailed('Неверный формат почты')

        user = User(request.app.client.energy_db.users)
        user = await user.get(email=email)
        if not user:
            logger.error('Пользователя не существует')
            raise PasswordResetFailed('Пользователя с данной почтой не существует')

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

        user = User(request.app.client.energy_db.users)
        res = await user.update({"password": password}, email=email)
        if res is None:
            logger.error('Не удалось обновить пароль пользователя')
            raise PasswordResetFailed('Не удалось обновить пароль пользователя')
        
        return response.json({'hit': 0})

class ApproveEmail(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        user = User(request.app.client.energy_db.users)
        try:
            email = request.app.ts.loads(
                request.json['token'], 
                salt="approve-email-key",
                max_age=86400
            )
        except Exception as e:
            res = await user.delete(email=email)
            if res is None:
                RegistrationFailed("Произошла ошибка")

            logger.error('Время действия ссылки истекло')
            raise RegistrationFailed("Время действия ссылки истекло")
        
        res = await user.update({"is_approve": True} , email=email)
        if res is None:
            raise RegistrationFailed("Не удалось подтвердить пользователя")

        return response.json({'hit': 0})
