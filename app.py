from flask import Flask
from controllers import *
from models import db
from flask_restful import Resource, Api
from api import UserAPI

db.init_app(app)
with app.app_context():
    db.create_all()

api = Api(app)

api.add_resource(UserAPI, '/user')

if __name__ == "__main__":
    app.run(debug=True)