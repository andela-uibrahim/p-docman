import sys

sys.path.append("..")

from flask import jsonify, request, make_response, g
from flask_jwt import jwt 
import datetime
from functools import wraps

from config import app_configuration

Config = app_configuration["development"]

# define a user class
class CurrentUser(object):
    def __init__(self, user_id, role, username, exp):
        self.user_id = user_id
        self.role = role
        self.username = username
        self.exp = exp

    def __repr__(self):
        return ("<CurrentUser \n"
                "userId - {} \n"
                "username - {} \n"
                "exp - {} \n"
                "role - {} >").format(self.user_id, self.username,
                                       self.exp, self.role)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('Authorization')

        if not token:       
            return {'message' : 'loggin token required for this route', "status": "failed"
            }, 403

        unauthorized_response = {
            "status": "failed",
            "message": "Unauthorized. The authorization token supplied is"
                       " invalid"}, 401
        
        expired_response = {
            "status": "failed",
            "message": "The authorization token supplied is expired"
        }, 401

        try:
            # decode token
            payload = jwt.decode(token, Config.SECRET_KEY,
                                 options={"verify_signature": False})

        except jwt.ExpiredSignatureError:
            return expired_response
        except jwt.InvalidTokenError:
            return unauthorized_response
     
        # instantiate user object
        current_user = CurrentUser(
            payload["user_id"], payload["role"],
            payload["username"],
            payload["exp"]
            )

        # set current user in flask global variable, g
        g.current_user = current_user

        return f(*args, **kwargs)

    return decorated

def generate_token(user):
    token = jwt.encode({"username" : user["username"], "role" : user["role"], "user_id" : user["id"],
                    "exp" : datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, Config.SECRET_KEY)
    return token.decode('UTF-8')