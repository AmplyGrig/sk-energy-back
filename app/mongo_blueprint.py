from sanic.response import json
from sanic import Blueprint
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

MONGO_CONN_STR = 'mongodb://root:example@localhost:27017'

mongo_bp = Blueprint('mongo_bp')

@mongo_bp.listener('before_server_start')
def init(app, loop):
    global client
    app.client = AsyncIOMotorClient(MONGO_CONN_STR,
        io_loop=asyncio.get_event_loop()
    )

@mongo_bp.listener('after_server_stop')
def disconnect_from_db(app, loop):
    app.client.close()