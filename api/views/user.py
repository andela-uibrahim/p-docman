import bcrypt

from datetime import datetime

from flask_jwt import jwt 
from flask import current_app, g, jsonify, request, url_for
from flask_restful import Resource

from ..auth import token_required, generate_token

from ..models import User, Document

from ..helpers import validate_type



class SignUp(Resource):

    # @token_required
    def post(self):

        if not request.json:
            return {"message": "Request must be a valid JSON", 
                    "status": "failed"}, 400

        payload = request.get_json()
        
        if payload:
            keys = ["username", "first_name", "last_name", "email", "password"]

            for key in keys:
                if key not in payload:
                    return {"message": key + " cannot be null",
                            "status": "failed"}, 400
                elif (not validate_type(payload[key], str)):
                    return {"message": key + " must be a valid string", 
                            "status": "failed"}, 400

                user = User.query.filter_by(username=payload["username"]).first()                
                if user:
                    return{
                        "status": "failed",
                        "error": "username already exist"}, 400  

                user = User.query.filter_by(email=payload["email"]).first()
                if user:
                    return{
                    "status": "failed",
                    "error": "email already exist"}, 400 
                
                payload["password"] = bcrypt.hashpw(payload["password"], bcrypt.gensalt())                
                user = User(username=payload["username"], email=payload["email"], password=payload["password"],
                    first_name=payload["first_name"], last_name=payload["last_name"])
                
                user.save()
                user = user.serialize()

                del user["password"]
                token = generate_token(user)
                user = {}
                user["token"] = token

                response = jsonify(dict(
                            data=user,
                            message="User has been successfully registered",
                            status="success"
                        ))
                response.status_code = 200
                
                return response