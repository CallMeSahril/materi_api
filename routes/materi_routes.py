from flask import send_from_directory, request
from flask_restx import Namespace, Resource, fields
from db import get_connection
from config import UPLOAD_FOLDER

api = Namespace('Materi', description='Manajemen data materi')

materi_model = api.model('Materi', {
    'id': fields.Integer,
    'bab': fields.String,
    'judul': fields.String,
    'status': fields.String,
    'filename': fields.String,
    'pdf_url': fields.String
})


@api.route('/')
class MateriList(Resource):
    @api.marshal_list_with(materi_model)
    def get(self):
        """Ambil semua data materi"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, bab, judul, status, filename FROM materi")
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        for m in data:
            # base_url = request.host_url.rstrip('/')
            base_url = "http://195.88.211.177:5006"
            m["pdf_url"] = f"{base_url}/uploads/{m['filename']}"
        return data


@api.route('/view/<int:materi_id>')
@api.param('materi_id', 'ID Materi')
class MateriPDF(Resource):
    def get(self, materi_id):
        """Tampilkan file PDF dari materi"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename FROM materi WHERE id = %s", (materi_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            filename = row[0]
            return send_from_directory(UPLOAD_FOLDER, filename)
        api.abort(404, "PDF tidak ditemukan")
