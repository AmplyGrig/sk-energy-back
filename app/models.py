from modules.database import DBHelper
from bson.objectid import ObjectId

class User:
    __slots__ = [
        'email', 
        'user_name',
        "phone",
        "company_name",
        "password",
        "is_approve",
        "register_date",
        "is_admin"
    ]
    def __init__(collection, **kwargs):
        self.users_collection = collection
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        properties = ['email', 'is_admin']
        return {prop: getattr(self, prop, None) for prop in properties}

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