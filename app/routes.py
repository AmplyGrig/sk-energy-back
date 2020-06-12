from app import protected, bcrypt, app
from sanic import response


from .email_sender import send_email
from .exception import PasswordResetFailed, RegistrationFailed
from modules.auth_register import ts
from modules.database import DBHelper

from email_validator import validate_email

@app.route('/', methods=['POST'])
@protected()
async def mainRoute(request):
    return text('sd')