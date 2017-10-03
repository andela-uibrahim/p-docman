import bcrypt

from datetime import datetime

from flask_jwt import jwt 
from flask import current_app, g, jsonify, request, url_for
from flask_restful import Resource
from sqlalchemy import or_

from ..auth import token_required

from ..models import db, User, Document

from ..helpers import validate_type



class CreateDocument(Resource):

    @token_required
    def post(self):

        if not request.json:
            return {"message": "Request must be a valid JSON", 
                    "status": "failed"}, 400

        payload = request.get_json()
        current_user = g.current_user
        payload["user_id"] = current_user.user_id
        
        if payload:
            keys = ["title", "content"]

            for key in keys:
                if key not in payload:
                    return {"message": key + " cannot be null",
                            "status": "failed"}, 400
                elif (not validate_type(payload[key], str)):
                    return {"message": key + " must be a valid string", 
                            "status": "failed"}, 400
            
            payload["access"] = payload.get("access", "public")
            user = User.query.get(current_user.user_id)
            if not user:
                return{
                "status": "failed",
                "error": "user does not exist"}, 400 

            document = Document.query.filter_by(title=payload["title"]).first()

            if document:
                return{
                    "status": "failed",
                    "error": "title already exist"}, 400  
                           
            document = Document(title=payload["title"], content=payload["content"], access=payload["access"],
                user_id=payload["user_id"])
            
            document.save()
            document = document.serialize()

            response = jsonify(dict(
                        data=document,
                        message="Document has been successfully created",
                        status="success"
                    ))
            response.status_code = 201
            
            return response

    @token_required
    def get(self):

        _page = request.args.get('page') if request.args.get('page') else 1
        _limit = request.args.get('limit') if request.args.get('limit') else 10
        page = int(_page) or 1
        limit = int(_limit) or 10
        search_term = request.args.get('q')
        current_user = g.current_user
        user_id = current_user.user_id
        role = current_user.role

        if role == "admin":
            _documents = Document.query.order_by(Document.created_at.desc()) 
        else:
            _documents = Document.query.filter(or_(Document.access=="public",
                                            Document.user_id==user_id)).order_by(Document.created_at.desc()) 
        if search_term:
            _documents = _documents.filter(Document.title.ilike("%"+search_term+"%"))

        _documents = _documents.paginate(page=page, per_page=limit, error_out=False)
        documents = []
        
        for document in _documents.items:
            document = document.serialize()
            documents.append(document)

        previous_url = None
        next_url = None

        if _documents.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _documents.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return jsonify(dict(count=(len(documents)), data=documents,
                            nextUrl=next_url, previousUrl=previous_url,
                            currentPage=_documents.page, status="success"))
        
        response.status_code = 200
        
        return response



class SingleDocument(Resource):
    
    @token_required
    def get(self, document_id):
        document = Document.query.get(document_id)
        current_user = g.current_user
        user_id = current_user.user_id
        role = current_user.role
        
        if not document:
            return{
                "status": "failed",
                "message": "document does not exist"}, 404
        
        access = document.access
        owner_id = document.user_id
        owner = User.query.get(owner_id)

        if user_id != owner_id and role != "admin":
            if access == "private" and role == "regular":
               return{
                "status": "failed",
                "message": "Unauthorised"}, 401

            if access == "role" and role != owner["role"]:
               return{
                "status": "failed",
                "message": "Unauthorised"}, 401
        
        document = document.serialize()

        response = jsonify(dict(
                            data=document,
                            status="success"
                        ))
        response.status_code = 200
        
        return response

    @token_required
    def put(self, document_id):

        document = Document.query.get(document_id)
        
        if not document:
            return{
                "status": "failed",
                "message": "document does not exist"}, 404

        current_user = g.current_user

        if current_user.user_id != document.user_id and current_user.role != "admin":
             return{
                "status": "failed",
                "message": "you are not authorized to carry out this operation"
                }, 401

        payload = request.get_json()

        keys = payload.keys()
        for key in keys:
            if key not in ["title", "content"]:
                keys.remove(key)
            else:
                setattr(document, key, payload[key])

        document.save()

        document = document.serialize()

        response = jsonify(dict(
                            data=document,
                            status="success"
                        ))
        response.status_code = 200
        
        return response

    @token_required
    def delete(self, document_id):

        document = Document.query.get(document_id)
        if not document:
            return{
                "status": "failed",
                "message": "document does not exist"}, 404

        current_user = g.current_user

        if current_user.user_id != document.user_id and current_user.role != "admin":
            return{
                "status": "failed",
                "message": "you are not authorized to carry out this operation"
            }, 401

        db.session.delete(document)
        db.session.commit()

        return {
                "status": "success",
                "message": "document has been successfully deleted"
            }, 200 

class UserDocuments(Resource):

    @token_required
    def get(self, userId):

        _page = request.args.get('page') if request.args.get('page') else 1
        _limit = request.args.get('limit') if request.args.get('limit') else 10
        page = int(_page) or 1
        limit = int(_limit) or 10
        search_term = request.args.get('q')

        current_user = g.current_user
        user_id = current_user.user_id
        role = current_user.role

        if role == "admin":
            _documents = Document.query.order_by(Document.created_at.desc()) 
        else:
            _documents = Document.query.filter(or_(Document.access=="public",
                                            Document.user_id==user_id)).order_by(Document.created_at.desc()) 
        if userId:
            _documents = _documents.filter_by(user_id=userId)
        
        _documents = _documents.paginate(page=page, per_page=limit, error_out=False)
        documents = []
        
        for document in _documents.items:
            document = document.serialize()
            documents.append(document)

        previous_url = None
        next_url = None

        if _documents.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _documents.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return jsonify(dict(count=(len(documents)), data=documents,
                            nextUrl=next_url, previousUrl=previous_url,
                            currentPage=_documents.page, status="success"))
        
        response.status_code = 200
        
        return response

