from modules.database import DBHelper
from bson.objectid import ObjectId
from modules.database import DBHelper
from typing import Dict
from .exception import UserException

class User(DBHelper):
    __slots__ = [
        'users_collection',
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
        self.users_collection = collection
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        properties = ['email', 'role']
        return {prop: getattr(self, prop, None) for prop in properties}

    async def insert(self):
        res = await super().async_select_db(self.users_collection, {"email" : self.email})
        if res:
            return 'Пользователь с данной электронной почтой уже зарегистрирован'

        row_to_insert = {}
        for slot in self.__slots__:
            if slot != 'users_collection' and slot != 'id':
                row_to_insert[slot] = getattr(self, slot)

        try:
            user = await super().insert_db(self.users_collection, row_to_insert)
        except:
            return 'Не удалось создать пользователя'

        self.id = user.inserted_id
        return None

    async def delete(self, **kwargs):
        row_ident_dict = {}
        for k, v in kwargs.items():
            row_ident_dict[k] = v
        try:
            return await super().delete_row(self.users_collection, row_ident_dict)
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
            user = await super().async_select_db(self.users_collection, row_idenc_dict)
        except:
            return None
        return user

    async def get_all(self, proection=None):
        try:
            users = await super().do_find(self.users_collection, {}, proection)
        except:
            return None
        return users

    async def update(self, update_dict, **kwargs):
        row_ident_dict = {}
        for k, v in kwargs.items():
            row_ident_dict[k] = v
        try:
            return await super().update_row(self.users_collection, row_ident_dict, {'$set' : update_dict})
        except Exception as e:
            return None

    @staticmethod
    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            db_helper = DBHelper()
            user = await db_helper.async_select_db(
                request.app.client.energy_db.users, 
                {'_id' : ObjectId(payload.get('user_id', None))}
            )
            return {
                'email': user.get('email', None),
                'role': user.get('role', None)
            }
        else:
            return None