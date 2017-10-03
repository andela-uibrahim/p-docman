import os
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_restful import Api

from config import app_configuration

from api.views.user import SignUp, Login, FetchAllUsers, SingleUser

from api.views.document import CreateDocument, SingleDocument, UserDocuments

def create_flask_app(environment):
    app = Flask(__name__, instance_relative_config=True, static_folder=None)
    
    app.config.from_object(app_configuration[environment])

    from api import models
   
    # initialize SQLAlchemy
    models.db.init_app(app)

    # initilize migration commands
    Migrate(app, models.db)
    
    # initilize api resources
    api = Api(app)

    # Landing page
    @app.route('/')
    def index():
        return "Welcome to the docman Api"

    # user endpoints
    api = Api(app)

    api.add_resource(SignUp,
                     '/api/users/signup',
                     '/api/users/signup',
                     endpoint='signup')
    
    api.add_resource(Login,
                    '/api/users/login',
                     '/api/users/login',
                     endpoint='login')
    
    api.add_resource(FetchAllUsers,
                    '/api/users',
                     '/api/users',
                     endpoint='fetch users')
    
    api.add_resource(SingleUser,
                    '/api/users/<int:user_id>',
                     '/api/users/<int:user_id>',
                     endpoint='single')

    # document endpoints
    api.add_resource(CreateDocument,
                    '/api/documents',
                     '/api/documents',
                     endpoint='documents')  

    api.add_resource(SingleDocument,
                    '/api/documents/<int:document_id>',
                     '/api/documents/<int:document_id>',
                     endpoint='singleDocument')

    api.add_resource(UserDocuments,
                    '/api/users/<int:userId>/documents',
                     '/api/users/<int:userId>/documents',
                     endpoint='UserDocuments')          
                     

    # handle default 404 exceptions with a custom response
    @app.errorhandler(404)
    def resource_not_found(error):
        response = jsonify(dict(status=404, error='Not found', message='The '
                                'requested URL was not found on the server. If'
                                ' you entered the URL manually please check '
                                'your spelling and try again'))
        response.status_code = 404
        return response

    # handle default 500 exceptions with a custom response
    @app.errorhandler(500)
    def internal_server_error(error):
        response = jsonify(dict(status=500, error='Internal server error',
                                message="It is not you. It is me. The server "
                                "encountered an internal error and was unable "
                                "to complete your request.  Either the server "
                                "is overloaded or there is an error in the "
                                "application"))
        response.status_code = 500
        return response

    return app


# enables flask commands
app = create_flask_app(os.getenv("FLASK_CONFIG"))
