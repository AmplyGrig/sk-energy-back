from app import app
from app import protected, DBHelper, ts, bcrypt
from .email_sender import send_email
from sanic import response
from .exception import PasswordResetFailed, RegistrationFailed
from email_validator import validate_email

@app.route('/', methods=['POST'])
@protected()
async def mainRoute(request):
    return text('sd')

@app.route('/reset-password', methods=['POST'])
async def reset_password_send_email(request):
    email = request.json.get('email', None)

    if validate_email(email):
        db_helper = DBHelper()
        user = await db_helper.async_select_db(app.client.energy_db.users, {"email" : email})
        if not user:
            raise PasswordResetFailed()

        token = ts.dumps(email, salt='recover-key')
        url = app.url_for('reset_password', token=token)
        url = 'http://localhost:8888' + url
        await send_email(email, "Восстановление пароля CK Energy", url)
        return response.json({'hit': 0})
    else:
        return response.json({'hit': 1})

@app.route('/reset-password-with-token', methods=['POST'])
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

@app.route('/approve-mail/<token>', methods=['GET'])
async def approve_email(request, token):
    try:
        email = ts.loads(token, salt="approve-email-key", max_age=86400)
    except:
        raise RegistrationFailed()
    
    db_helper = DBHelper()
    await db_helper.update_row(app.client.energy_db.users, {"email" : email}, { "$set": { "isapprove": True } })

    return response.json({'hit': 0})
    