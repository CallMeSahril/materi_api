from flask_restx import Namespace, Resource, fields
from flask import request
from db import get_connection

api = Namespace('musik', description='API untuk data musik')

musik_model = api.model('Musik', {
    'id': fields.Integer,
    'nama': fields.String,
})


@api.route('/')
class MusikList(Resource):
    @api.marshal_list_with(musik_model)
    def get(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama FROM musik ORDER BY id ASC")
        hasil = cursor.fetchall()
        cursor.close()
        conn.close()
        return hasil
