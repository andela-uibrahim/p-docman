import bcrypt

from datetime import datetime

from flask_jwt import jwt 
from flask import current_app, g, jsonify, request, url_for
from flask_restful import Resource

from sqlalchemy import or_

from ..auth import token_required, generate_token

from ..models import db, User, Document

from ..helpers import validate_type



class SignUp(Resource):

    # @token_required
    def post(self):

        if not request.json:
            return {"message": "Request must be a valid JSON", 
                    "status": "failed"}, 400
        current_user = g.current_user
        
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

                if current_user:
                    if current_user.role == "admin":
                        user = User(username=payload["username"], email=payload["email"], password=payload["password"],
                        first_name=payload["first_name"], last_name=payload["last_name"], role=payload["role"]) 
                else:               
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

class Login(Resource):

    # @token_required
    def post(self):

        if not request.json:
            return {"message": "Request must be a valid JSON", 
                    "status": "failed"}, 400

        payload = request.get_json()
        
        if payload:
            keys = ["username", "password"]

            for key in keys:
                if key not in payload:
                    return {"message": key + " cannot be null",
                            "status": "failed"}, 400
                elif (not validate_type(payload[key], str)):
                    return {"message": key + " must be a valid string", 
                            "status": "failed"}, 400

                user = User.query.filter_by(username=payload["username"]).first()                
                if not user:
                    return{
                        "status": "failed",
                        "error": "username does not exist"}, 400

                valid_password = user.verify_password(payload["password"])   
                
                if not valid_password:
                    return{
                        "status": "failed",
                        "message": "Invalid password"}
                
                user = user.serialize()

                del user["password"]
                token = generate_token(user)
                user = {}
                user["token"] = token

                response = jsonify(dict(
                            data=user,
                            message="User has been successfully Logged In",
                            status="success"
                        ))
                response.status_code = 200
                
                return response


class FetchAllUsers(Resource):

    @token_required
    def get(self):

        _page = request.args.get('page') if request.args.get('page') else 1
        _limit = request.args.get('limit') if request.args.get('limit') else 10
        page = int(_page) or 1
        limit = int(_limit) or 10
        search_term = request.args.get('q')
        _users = User.query.order_by(User.created_at.desc())  

        if search_term:

            _users = _users.filter(or_(User.first_name.ilike("%"+search_term+"%"),
             User.last_name.ilike("%"+search_term+"%"), User.username.ilike("%"+search_term+"%"),
             User.email.ilike("%"+search_term+"%")))

        _users = _users.paginate(page=page, per_page=limit, error_out=False)
        users = []
        
        for user in _users.items:
            user = user.serialize()
            del user["password"]
            users.append(user)

        previous_url = None
        next_url = None

        if _users.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _users.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return jsonify(dict(count=(len(users)), data=users,
                            nextUrl=next_url, previousUrl=previous_url,
                            currentPage=_users.page, status="success"))
        
        response.status_code = 200
        
        return response

class SingleUser(Resource):
    
    @token_required
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return{
                "status": "failed",
                "message": "user does not exist"}, 404
        
        user = user.serialize()
        del user["password"]

        response = jsonify(dict(
                            data=user,
                            status="success"
                        ))
        response.status_code = 200
        
        return response

    @token_required
    def put(self, user_id):

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return{
                "status": "failed",
                "message": "user does not exist"}, 404

        current_user = g.current_user

        if current_user.user_id != user.id and current_user.role != "admin":
             return{
                "status": "failed",
                "message": "you are not authorized to carry out this operation"
                }, 401

        payload = request.get_json()

        keys = payload.keys()
        for key in keys:
            if key not in ["username", "first_name", "last_name", "email", "password"]:
                keys.remove(key)
            else:
                setattr(user, key, payload[key])

        user.save()

        user = user.serialize()
        del user["password"]

        response = jsonify(dict(
                            data=user,
                            status="success"
                        ))
        response.status_code = 200
        
        return response

    @token_required
    def delete(self, user_id):

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return{
                "status": "failed",
                "message": "user does not exist"}, 404

        current_user = g.current_user

        if current_user.user_id != user.id and current_user.role != "admin":
            return{
                "status": "failed",
                "message": "you are not authorized to carry out this operation"
            }, 401

        db.session.delete(user)
        db.session.commit()

        return {
                "status": "success",
                "message": "user account has been successfully deleted"
            }, 200

