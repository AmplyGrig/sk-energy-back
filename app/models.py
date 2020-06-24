from modules.database import DBHelper
from bson.objectid import ObjectId
from modules.database import DBHelper
from typing import Dict
from .exception import UserException

class User(DBHelper):
    __slots__ = [
        'collection',
        'id',
        'email', 
        'user_name',
        "phone",
        "company_name",
        "password",
        "is_approve",
        "register_date",
        "role"
    ]
    def __init__(self, collection, **kwargs):
        self.collection = collection
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        properties = ['email', 'role']
        return {prop: getattr(self, prop, None) for prop in properties}

    async def insert(self):
        res = await super()._select_db(self.collection, {"email" : self.email})
        if res:
            return 'Пользователь с данной электронной почтой уже зарегистрирован'

        row_to_insert = {}
        for slot in self.__slots__:
            if slot != 'collection' and slot != 'id':
                row_to_insert[slot] = getattr(self, slot)

        try:
            user = await super()._insert_db(self.collection, row_to_insert)
        except:
            return 'Не удалось создать пользователя'

        self.id = user.inserted_id
        return None

    async def delete(self, **kwargs):
        row_ident_dict = {}
        for k, v in kwargs.items():
            row_ident_dict[k] = v
        try:
            return await super()._delete_db(self.collection, row_ident_dict)
        except:
            return None

    def get_id(self) -> ObjectId:
        return self.id

    async def get(self, **kwargs):
        row_idenc_dict = {}
        for k, v in kwargs.items():
            for slot in self.__slots__:
                if k == slot:
                    row_idenc_dict[k] = v
                if k == 'id':
                    row_idenc_dict['_id'] = v
        try:
            user = await super()._select_db(self.collection, row_idenc_dict)
        except:
            return None
        return user

    async def get_all(self, proection=None):
        try:
            users = await super()._find_db(self.collection, {}, proection)
        except:
            return None
        return users

    async def update(self, update_dict, **kwargs):
        row_ident_dict = {}
        for k, v in kwargs.items():
            row_ident_dict[k] = v
        try:
            return await super()._update_db(self.collection, row_ident_dict, {'$set' : update_dict})
        except Exception as e:
            return None

    @staticmethod
    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            db_helper = DBHelper()
            user = await db_helper._select_db(
                request.app.client.energy_db.users, 
                {'_id' : ObjectId(payload.get('user_id', None))}
            )
            return {
                'email': user.get('email', None),
                'role': user.get('role', None)
            }
        else:
            return None

class Object(DBHelper):
    __slots__ = [
        'collection',
        'id',
        'object_name', 
        'user_email',
        'change_dt',
        'passport_pute',
        'project_uute',
        'tech_conditions',
        'tech_passport',
        'cadastr_passport',
        'recvisits'
    ]

    def __init__(self, collection, **kwargs):
        self.collection = collection
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self):
        res = await super()._select_db(self.collection, {"object_name" : self.object_name})
        if res:
            return None, 'Объект с данным именем уже создан'

        row_to_insert = {}
        for slot in self.__slots__:
            if slot == 'object_name' or slot == 'user_email':
                row_to_insert[slot] = getattr(self, slot)

        new_object = await super()._insert_db(self.collection, row_to_insert)
        if not new_object.inserted_id:
            return None, 'Не удалось создать объект'

        self.id = new_object.inserted_id

        return new_object.inserted_id, None

    async def select(self, row_ident: dict, proection: dict = None, isFiles:bool = None, fileFieldsNeed:list = None) -> list:
        if isFiles:
            list_of_keys = [
                'passport_pute',
                'project_uute',
                'tech_conditions',
                'tech_passport',
                'cadastr_passport',
                'recvisits',
            ]

            if not proection:
                proection = {}

            for main_file_name in list_of_keys:
                for files_slot in File.__slots__:
                    if files_slot not in fileFieldsNeed:
                        proection_key = '{0}.{1}'.format(main_file_name, files_slot)
                        proection[proection_key] = False

            res = await super()._find_db(
                self.collection, 
                row_ident,
                proection
            )

        else:
            res = await super()._find_db(
                self.collection, 
                row_ident, 
                proection
            )

        if proection.get('_id') == True:
            for item in res:
                item['_id'] = str(item['_id'])
        
        return res, None
    
    async def delete(self, row_ident: dict):
        res = await super()._delete_db(
            self.collection, 
            row_ident
        )
        if not res:
            return None, "Не удалось удалить объект"

        return res, None

    async def update(self, row_ident: dict, row_update: dict):
        res = await super()._update_db(
            self.collection, 
            row_ident, 
            { "$set": row_update }
        )
        if not res:
            return None, "Не удалось обновить информацию объекта"
        
        return res, None

    async def push(self, row_ident: dict, row_push: dict):
        res = await super()._update_db(
            self.collection, 
            row_ident, 
            { "$push": row_push }
        )
        if not res:
            return None, "Не удалось добавить информацию к объекту"
        
        return res, None

    async def get_user(self, object_id):
        pipeline = [
            {'$lookup': {
                    'localField': 'user_email',
                    'from': 'users',
                    'foreignField': 'email',
                    'as': 'users' 
                },
            },
            { "$unwind":"$users" },
            { '$match': {'_id' : ObjectId(object_id)} },
            { "$project": {
                "users.email": 1,
                "users.user_name": 1,
                "users.phone": 1,
                "users.company_name": 1,
                }
            },
        ]
        res = await super()._aggregate(self.collection, pipeline)
        if not res:
            return None, "Не удалось получить информацию о пользователе"
        return res[0]['users'], None

class File(DBHelper):
    __slots__ = [
        "type",
        "content",
        "filename",
        "is_approve",
        "comment"
    ]