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
from sanic.log import logger
from datetime import datetime
import bson


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

@app.route('/get-my-user', methods=["GET"])
@inject_user()
@scoped('user')
@protected()
async def get_my_user(request, user):
    users = User(app.client.energy_db.users)
    email = user['email']
    myuser = await users.get(email=email)
    myuser.pop('_id', None)
    myuser.pop('register_date', None)
    logger.error(myuser)
    return response.json(myuser)



@app.route('/get-notify-count', methods=["GET"])
@inject_user()
@scoped('user')
@protected()
async def get_notify_count(request, user):
    obj = Object(app.client.energy_db.objects)
    obj_list, err = await obj.select(
        { 'user_email': user['email'] },
        {           
            "object_name": False, 
            "user_email": False,
            "change_dt": False},
        isFiles=True,
        fileFieldsNeed=['is_approve', 'comment']
    )
    db_helper = DBHelper()
    count = 0

    for value in obj_list:
        res = await db_helper._find_db(app.client.energy_db.files,
        {
            "object_id": str(value['_id']),
            "is_approve": False
        },
        { "file_key": 1,"comment": 1 }
        )
        if res:
            for el in res:
                if (el['comment'] != ''):
                    count += 1
        value.pop('_id', None)
        for val in value:
            if (value[val]['comment'] != ''):
                count += 1
    
    

    return response.json({'messages':count})

@app.route('/get-notify-list', methods=["GET"])
@inject_user()
@scoped('user')
@protected()
async def get_notify_list(request, user):
    obj = Object(app.client.energy_db.objects)
    obj_list, err = await obj.select(
        { 'user_email': user['email'] },
        {           
            "user_email": False,
            "change_dt": False},
        isFiles=True,
        fileFieldsNeed=['is_approve', 'comment']
    )
    db_helper = DBHelper()
    count = 0
    tmp = []

    for value in obj_list:
        object_name = value['object_name']
        res = await db_helper._find_db(app.client.energy_db.files,
        {
            "object_id": str(value['_id']),
            "is_approve": False
        },
        { "file_key": 1,"comment": 1,"year": 1,"month": 1}
        )
        if res:
            for el in res:
                if (el['comment'] != ''):
                    month = '0'
                    if (el['month'] != 'null'):
                        month = el['month']
                    tmp.append({'object':object_name,'file_type':el['file_key'],'comment':el['comment'],'year':str(el['year']),'month':str(month)})
        value.pop('_id', None)
        value.pop('object_name', None)
        for val in value:
            if (value[val]['comment'] != ''):
                tmp.append({'object':object_name,'file_type':val,'comment':value[val]['comment'],'year':'','month':'0'})
    
    

    return response.json({'notify':tmp})


@app.route('/update-my-user', methods=["POST"])
@inject_user()
@scoped('user')
@protected()
async def update_my_user(request, user):
    users = User(app.client.energy_db.users)
    email = user['email']
    obj = {}
    # for key, value in request.json:
    #     obj
    
    myuser = await users.update(request.json, email=email)

    return response.json(200)

@app.route('/add-object', methods=["POST"])
@inject_user()
@scoped('user')
@protected()
async def add_object(request, user):
    new_object = Object(
        app.client.energy_db.objects, 
        object_name=request.json['object_name'], 
        user_email=user['email'],
        change_dt = str(datetime.now())
    )
    res, err = await new_object.insert()
    if err:
        print(err)
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
            "change_dt": str(datetime.now()),
            object_type: {
                "type": object_file.type,
                "content": object_file.body,
                "filename": object_file.name,
                "is_approve": False,
                "comment": ''
            }
        }
    )
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})

@app.route('/upload-file', methods=['POST'])
@inject_user()
@scoped('user')
@protected()
async def upload_file(request, user):
    file = request.files['file'][0]
    db_helper = DBHelper()
    month = 'null'
    if (request.form['file_month'][0] != 'null'):
        month = int(request.form['file_month'][0])
    res = await db_helper._find_db(app.client.energy_db.files,
        {
            'file_key': request.form['file_type'][0],
            "object_id": request.form['object_id'][0],
            "year": request.form['file_year'][0],
            "month": month
        },
        { "_id": 1 }
    )
    if res:
        res = await db_helper._update_db(app.client.energy_db.files, 
            {
                'file_key': request.form['file_type'][0],
                "year": request.form['file_year'][0],
                "month": month,
                "object_id": request.form['object_id'][0]
            },
            { "$set": {
                    'file_key': request.form['file_type'][0],
                    "year": request.form['file_year'][0],
                    "month": month,
                    "object_id": request.form['object_id'][0],
                    "type": file.type,
                    "content": file.body,
                    "filename": file.name,
                    "is_approve": False,
                    "comment": ''
                }
            })
    else:
        res = await db_helper._insert_db(app.client.energy_db.files, {
            'file_key': request.form['file_type'][0],
            "year": request.form['file_year'][0],
            "month": month,
            "object_id": request.form['object_id'][0],
            "type": file.type,
            "content": file.body,
            "filename": file.name,
            "is_approve": False,
            "comment": ''
        })
    if not res:
        raise ObjectException('Не удалось загрузить файл')
    obj = Object(app.client.energy_db.objects)
    res, err = await obj.update(
        {"_id": ObjectId(request.form['object_id'][0])},
        {
            "change_dt": str(datetime.now()),
        }
    )

    return response.json({'hit': 0})

@app.route('/upload-files', methods=['POST'])
@inject_user()
@scoped('user')
@protected()
async def upload_files(request, user):
    db_helper = DBHelper()
    for key in request.files:
        file = request.files[key][0]
        try:
            metaFile = file.name.split('.')
            metaFile = metaFile[0].split('-')
        except:
            raise ObjectException('Ошибка в названии файла: {0}'.format(file.name))

        try:
            month = int(metaFile[1])
            if month not in list(range(1, 13)):
                raise ObjectException('Ошибка в названии файла: {0}'.format(file.name))

            year = int(metaFile[0])
            if (year < 2017) or (year > 2100) or (int(request.form['file_year'][0]) != year):
                raise ObjectException('Ошибка в названии файла: {0}'.format(file.name))
        except:
            raise ObjectException('Ошибка в названии файла: {0}'.format(file.name))
        res = await db_helper._find_db(app.client.energy_db.files,
            {
                'file_key': request.form['file_type'][0],
                "object_id": request.form['object_id'][0],
                "year": request.form['file_year'][0],
                "month": month
            },
            { "_id": 1 }
        )
        if res:
            res = await db_helper._update_db(app.client.energy_db.files, 
                {
                    'file_key': request.form['file_type'][0],
                    "year": request.form['file_year'][0],
                    "month": month,
                    "object_id": request.form['object_id'][0]
                },
                { "$set": {
                        'file_key': request.form['file_type'][0],
                        "year": request.form['file_year'][0],
                        "month": month,
                        "object_id": request.form['object_id'][0],
                        "type": file.type,
                        "content": file.body,
                        "filename": file.name,
                        "is_approve": False,
                        "comment": ''
                    }
                })
        else:
            res = await db_helper._insert_db(app.client.energy_db.files, {
                'file_key': request.form['file_type'][0],
                "year": request.form['file_year'][0],
                "month": month,
                "object_id": request.form['object_id'][0],
                "type": file.type,
                "content": file.body,
                "filename": file.name,
                "is_approve": False,
                "comment": ''
            })
        if not res:
            raise ObjectException('Не удалось загрузить файл: {0}'.format(file.name))

    return response.json({'hit': 0})
    
@app.route('/get-main-files', methods=['POST'])
@inject_user()
@protected()
async def get_main_files(request, user):
    obj = Object(app.client.energy_db.objects)
    res, err = await obj.select(
        { '_id': ObjectId(request.json['object_id'])    },
        {
            "_id": False,
            "object_name": False, 
            "user_email": False,
            "change_dt": False
        },
        isFiles=True,
        fileFieldsNeed=['is_approve', 'comment']
    )
    print(res)
    if err:
        raise ObjectException(err)
    return response.json({'uploaded_files' : res[0]})

@app.route('/get-files', methods=['POST'])
@inject_user()
@protected()
async def get_files(request, user):
    print(request.json)
    db_helper = DBHelper()
    res = await db_helper._find_db(app.client.energy_db.files,
        { 'object_id': request.json['object_id'], 'file_key': request.json['file_type']},
        { 'content': 0 }
    )

    for item in res:
        item['_id'] = str(item['_id'])

    return response.json(res)

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
            {'_id': True, 'object_name': True, 'change_dt': True}
        )
        if err:
            raise ObjectException(err)

        for objectt in objects:
            res.append({
                'user_name': user['user_name'],
                'object_name': objectt['object_name'],
                'change_time': objectt['change_dt'],
                'object_id': str(objectt['_id']),
            })
    return response.json({"users": res})

@app.route('/get-user-info', methods=['POST'])
@protected()
@scoped('admin')
async def get_user_info(request):
    obj = Object(app.client.energy_db.objects)
    res, err = await obj.get_user(request.json['object_id'])
    if err:
        raise ObjectException(err)
    return response.json(res)

@app.route('/download-main-file', methods=['POST'])
@inject_user()
@scoped('admin')
@protected()
async def download_main_file(request, user):
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

@app.route('/download-file', methods=['POST'])
@inject_user()
@scoped('admin')
@protected()
async def download_file(request, user):
    print(request.json)
    db_helper = DBHelper()
    month = 'null'
    if 'file_month' in request.json:
        month = int(request.json['file_month'])
    res = await db_helper._select_db(app.client.energy_db.files,
        {
            "object_id": request.json['object_id'],
            "year": str(request.json['file_year']),
            "month": month,
            "file_key": request.json['file_key'],
        }
    )
    print(res)
    return response.HTTPResponse(
        status=200,
        headers={"Content-Disposition": 'attachment; filename="{0}"'.format(res['filename'])},
        content_type=res['type'],
        body_bytes=res['content'],
    )

@app.route('/add-comment-to-main-file', methods=['POST'])
@scoped('admin')
@protected()
async def add_comment_to_main_file(request):
    object_id = ObjectId(request.json['object_id'])
    object_key = request.json['object_key']
    comment = request.json['comment']

    obj = Object(app.client.energy_db.objects)
    res, err = await obj.update(
        {"_id": object_id},
        { 
            object_key+'.comment':comment 
        }
    )
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})

@app.route('/add-comment-to-file', methods=['POST'])
@scoped('admin')
@protected()
async def add_comment_to_file(request):
    print(request.json)
    db_helper = DBHelper()
    month = 'null'
    if 'file_month' in request.json:
        month = int(request.json['file_month'])
    res = await db_helper._update_db(
        app.client.energy_db.files,
        {
            "object_id": request.json['object_id'],
            "year": str(request.json['file_year']),
            "month": month,
            "file_key": request.json['file_key'],
        },
        {
            "$set" : {
                'comment': request.json['comment']
            }
        }
    )
    print(res)
    if not res:
        raise ObjectException('Не удалось добавить комментарий')

    return response.json({'hit': 0})

@app.route('/approve-main-file', methods=['POST'])
@scoped('admin')
@protected()
async def approve_main_file(request):
    object_id = ObjectId(request.json['object_id'])
    object_key = request.json['object_key']

    obj = Object(app.client.energy_db.objects)
    res, err = await obj.update(
        {"_id": object_id},
        { object_key + '.is_approve': True }
    )
    if err:
        raise ObjectException(err)

    return response.json({'hit': 0})


@app.route('/approve-file', methods=['POST'])
@scoped('admin')
@protected()
async def approve_file(request):
    print(request.json.get('file_month', "null"))
    db_helper = DBHelper()
    month = 'null'
    if 'file_month' in request.json:
        month = int(request.json['file_month'])
    res = await db_helper._update_db(
        app.client.energy_db.files,
        {
            "object_id": request.json['object_id'],
            "year": str(request.json['file_year']),
            "month": month,
            "file_key": request.json['file_key'],
        },
        {
            "$set" : {
                'is_approve': True
            }
        }
    )
    print(res)
    if not res:
        raise ObjectException('Не удалось подтвердить файл')

    return response.json({'hit': 0})
