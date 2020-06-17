from app import app
from sanic_jwt import protected, inject_user
from sanic import response
from modules.email_sender import send_email
from email_validator import validate_email
import json
from modules.database import DBHelper
from bson.objectid import ObjectId
from .models import User, Object
from .exception import ObjectException
from sanic_jwt.decorators import scoped

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
@scoped('user')
@protected()
async def add_object(request, user):
    new_object = Object(
        app.client.energy_db.objects, 
        object_name=request.json['object_name'], 
        user_email=user['email']
    )
    res, err = await new_object.insert()
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})
    
@app.route('/get-object-list', methods=["GET"])
@inject_user()
@protected()
async def get_object_list(request, user):
    obj = Object(app.client.energy_db.objects)
    obj_list, err = await obj.select(
        { 'user_email': user['email'] }, 
        {"_id": True, "object_name": True}
    )
    if err:
        raise ObjectException(err)

    return response.json({'objects' : obj_list})
    
@app.route('/get-object', methods=["POST"])
@inject_user()
@protected()
async def get_object(request, user):
    obj = Object(app.client.energy_db.objects)
    obj_list, err = await obj.select(
        { 'user_email': user['email'] }
    )
    if err:
        raise ObjectException(err)

    return response.json({'objects' : obj_list})

@app.route('/delete-object', methods=['POST'])
@inject_user()
@scoped('user')
@protected()
async def delete_object(request, user):
    obj = Object(app.client.energy_db.objects)
    res, err = await obj.delete({
            '_id': ObjectId(request.json['object_id']), 
            'user_email' : user['email'], 
            'object_name': request.json['object_name']
    })
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})

@app.route('/upload-main-file', methods=['POST'])
@inject_user()
@scoped('user')
@protected()
async def upload_main_file(request, user):
    object_id = ObjectId(request.form['object_id'][0])
    object_type = request.form['object_type'][0]
    object_file = request.files['object_file'][0]

    obj = Object(app.client.energy_db.objects)
    res, err = await obj.update(
        {"_id": object_id},
        {
            object_type: {
                "type": object_file.type,
                "content": object_file.body,
                "filename": object_file.name,
                "is_approve": False
            }
        }
    )
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})

@app.route('/get-main-files', methods=['POST'])
@inject_user()
@protected()
async def get_main_files(request, user):
    obj = Object(app.client.energy_db.objects)
    res, err = await obj.select(
        { 'user_email': "leonid_kit@mail.ru", '_id': ObjectId(request.json['object_id'])},
        {
            "_id": False,
            "object_name": False, 
            "user_email": False
        },
        isFiles=True,
        fileFieldsNeed=['is_approve']
    )
    
    if err:
        raise ObjectException(err)
    
    return response.json({'uploaded_files' : res[0]})

@app.route('/get-users', methods=['GET'])
@inject_user()
@protected()
async def get_users(request, user):
    res = []
    user = User(app.client.energy_db.users)
    users = await user.get_all({'_id': False, 'email': True, 'user_name': True})

    obj = Object(app.client.energy_db.objects)
    for user in users:
        objects, err = await obj.select(
            {'user_email' : user['email']}, 
            {'_id': True, 'object_name': True}
        )
        if err:
            raise ObjectException(err)

        for objectt in objects:
            res.append({
                'user_name': user['user_name'],
                'object_name': objectt['object_name'],
                'object_id': str(objectt['_id']),
            })
    return response.json({"users": res})


@app.route('/download-file', methods=['POST'])
@inject_user()
@scoped('admin')
@protected()
async def download_file(request, user):
    obj = Object(app.client.energy_db.objects)

    res, err = await obj.select(
        { '_id' : ObjectId(request.json['object_id']) }, 
        { request.json['object_key']: True }
    )
    if err:
        raise ObjectException(err)

    return response.HTTPResponse(
        status=200,
        headers={"Content-Disposition": 'attachment; filename="{0}"'.format(res[0][request.json['object_key']]['filename'])},
        content_type=res[0][request.json['object_key']]['type'],
        body_bytes=res[0][request.json['object_key']]['content'],
    )