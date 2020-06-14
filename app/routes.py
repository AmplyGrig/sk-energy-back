from app import app
from sanic_jwt import protected, inject_user
from sanic import response
from modules.email_sender import send_email
from email_validator import validate_email
import json
from modules.database import DBHelper
from bson.objectid import ObjectId
from .models import User

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

@app.route('/add-object', methods=["POST"])
@inject_user()
@protected()
async def add_object(request, user):
    req_json = json.loads(request.body)
    print(user)
    #TODO: Проверить есть ли в бд объект с тем же именем
    db_helper = DBHelper()
    res = await db_helper.insert_db(app.client.energy_db.objects, {
            'object_name': req_json['object_name'],
            'user_email': user['email']
        }
    )
    return response.json({'hit': 0})
    
#TODO сделать два метода 1) отдает инфу для отрисовки слева в меню 2) отдает полностью содерждиморе для всего    
@app.route('/get-object-list', methods=["GET"])
@inject_user()
@protected()
async def get_object_list(request, user):
    db_helper = DBHelper()
    res = await db_helper.do_find(
        app.client.energy_db.objects, 
        { 'user_email': user['email'] }, 
        {"_id": True, "object_name": True}
    )
    for item in res:
        item['_id'] = str(item['_id'])
    return response.json({'objects' : res})
    
@app.route('/get-object', methods=["POST"])
@inject_user()
@protected()
async def get_object(request, user):
    db_helper = DBHelper()
    res = await db_helper.do_find(app.client.energy_db.objects, { 'user_email': user['email'] })
    for item in res:
        item['_id'] = str(item['_id'])
    return response.json({'objects' : res})

@app.route('/delete-object', methods=['POST'])
@inject_user()
@protected()
async def delete_object(request, user):
    email = user['email']
    req_json = json.loads(request.body)
    object_name = req_json['object_name']
    object_id = req_json['object_id']
    db_helper = DBHelper()

    res = await db_helper.delete_row(
        app.client.energy_db.objects, 
        {
            '_id': ObjectId(object_id), 
            'user_email' : email, 
            'object_name': object_name
        }
    )
    print(res)

    return response.json({'hit': 0})

@app.route('/upload-main-file', methods=['POST'])
@inject_user()
@protected()
async def upload_main_file(request, user):
    print(request.form)
    object_id = ObjectId(request.form['object_id'][0])
    object_type = request.form['object_type'][0]
    object_file = request.files['object_file'][0]

    db_helper = DBHelper()
    res = await db_helper.update_row(
        app.client.energy_db.objects, 
        {"_id": object_id}, 
        {
            "$set": {
                object_type: {
                    "type": object_file.type,
                    "content": object_file.body,
                    "filename": object_file.name,
                    "is_approve": False
                }
            }
        }
    )
    print((res.raw_result))
    return response.text('sdadf')

@app.route('/get-main-files', methods=['POST'])
@inject_user()
@protected()
async def get_main_files(request, user):
    db_helper = DBHelper()
    res = await db_helper.do_find(
        app.client.energy_db.objects, 
        { 'user_email': user['email'], '_id': ObjectId(request.json['object_id']) }, 
        {"_id": False, "object_name": False, "user_email": False}
    )
    print((res))
    list_of_keys = [
        'passport_pute',
        'project_uute',
        'tech_conditions',
        'tech_passport',
        'cadastr_passport',
        'recvisits',
    ]
    ret = {}
    if res:
        for key in list_of_keys:
            if res[0].get(key, None):
                ret[key] = True

    print(ret)
    return response.json({'uploaded_files' : ret})

@app.route('/get-users', methods=['GET'])
@inject_user()
@protected()
async def get_users(request, user):
    res = []
    db_helper = DBHelper()
    user = User(app.client.energy_db.users)
    users = await user.get_all({'_id': False, 'email': True, 'user_name': True})
    for user in users:
        objects = await db_helper.do_find(
            app.client.energy_db.objects, 
            {'user_email' : user['email']}, 
            {'_id': True, 'object_name': True}
        )
        for objectt in objects:
            res.append({
                'user_name': user['user_name'],
                'object_name': objectt['object_name'],
                'object_id': str(objectt['_id']),
            })
    return response.json({"users": res})


@app.route('/download-file', methods=['POST'])
@inject_user()
@protected()
async def download_file(request, user):
    print(request.json)

    db_helper = DBHelper()

    res = await db_helper.async_select_db(app.client.energy_db.objects, {'_id' : ObjectId(request.json['object_id'])}, {request.json['object_key']: True})
    print((res[request.json['object_key']]['type']))
    return response.HTTPResponse(
        status=200,
        headers={"Content-Disposition": 'attachment; filename="{0}"'.format({res[request.json['object_key']]['filename']})},
        content_type=res[request.json['object_key']]['type'],
        body_bytes=res[request.json['object_key']]['content'],
    )