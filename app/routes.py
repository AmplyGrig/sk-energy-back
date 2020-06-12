from app import app
from sanic_jwt import protected
from sanic import response

@app.route('/', methods=['POST'])
@protected()
async def mainRoute(request):
    return response.text('sd')