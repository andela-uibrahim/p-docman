import sys

sys.path.append("..")

from flask import jsonify, request, make_response
from flask_jwt import jwt 
import datetime
from functools import wraps

from config import app_configuration

Config = app_configuration["development"]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') #http://127.0.0.1:5000/route?token=alshfjfjdklsfj89549834ur

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try: 
            data = jwt.decode(token, app_configuration['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated

def generate_token(user):
    token = jwt.encode({"username" : user["username"], "role" : user["role"],
                    "exp" : datetime.datetime.utcnow() + datetime.timedelta(seconds=15)}, Config.SECRET_KEY)
    return token.decode('UTF-8')