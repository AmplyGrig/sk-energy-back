from app import app
from sanic_jwt import protected
from sanic import response
from modules.email_sender import send_email
from email_validator import validate_email
import json

@app.route('/', methods=['POST'])
@protected()
async def mainRoute(request):
    return response.text('sd')

@app.route('/call-me', methods=['POST',])
async def callMe(request):
    email = request.json['email']
    try:
        validate_email(email)
    except:
        return response.json({'hit': 1})
    try:
        msg = """
            Имя: {0}
            Номер телефона: {1}
            Почтовый адрес: {2}
        """.format(request.json['name'], request.json['phone'], request.json['email'])
        await send_email(app.config['CORP_EMAIL'], 'Новая заявка на звонок', msg)
    except Exception as e:
        return response.json({'hit': 1})

    return response.json({'hit': 0})