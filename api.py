from flask_restful import Resource


class UserAPI(Resource):
    def get(self):
        return {'hello': 'user'}
    def put(self):
        pass
    def delete(self):
        pass
    def post(self):
        pass