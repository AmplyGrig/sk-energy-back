from sanic_jwt import BaseEndpoint
from modules.email_sender import send_email
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
from .database import DBHelper
from app.exception import RegistrationFailed
from sanic.log import logger
from sanic.response import json
from app.models import User

class Register(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        response = json({})
        request_json = request.json
        try:
            email = request_json['email']
            email_valid = validate_email(email)
        except EmailNotValidError as e:
            logger.error("Неверный формат почты - {0}".format(str(e)))
            raise RegistrationFailed("Неверный формат почты")

        user = User(
            request.app.client.energy_db.users, 
            email=request_json['email'],
            user_name=request_json['user_name'],
            phone=request_json['phone'],
            company_name=request_json['company_name'],
            password=request.app.bcrypt.generate_password_hash(request_json['password']).decode('utf-8'),
            is_approve=False,
            register_date=datetime.now(),
            role=['user']
        )

        res = await user.insert()
        if res:
            logger.error(res)
            raise RegistrationFailed(res)
        else:
            try:
                token = request.app.ts.dumps(email, salt='approve-email-key')
                url = request.url_for('auth_bp.ApproveEmail', token=token)
                await send_email(email, "Подтверждение регистрации CK Energy", url)
            except Exception as e:
                await user.delete()
                logger.error("Не удалось отправить письмо с подтверждением на почту - {0}".format(request_json['email']))
                raise RegistrationFailed("Не удалось отправить письмо с подтверждением")

            response = json({'user_id': str(user.get_id())})

        return response
