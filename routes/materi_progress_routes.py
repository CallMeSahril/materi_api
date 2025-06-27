from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('ProgressMateri', description='Progress pengguna terhadap materi')

materi_progress_model = api.model('MateriProgress', {
    'id': fields.Integer,
    'bab': fields.String,
    'judul': fields.String,
    'filename': fields.String,
    'is_watched': fields.Boolean,
    'is_completed': fields.Boolean,
    'watched_at': fields.String,
    'completed_at': fields.String
})


@api.route('/<int:user_id>')
@api.param('user_id', 'ID Pengguna')
class MateriProgressList(Resource):
    @api.marshal_list_with(materi_progress_model)
    def get(self, user_id):
        """Ambil progress materi berdasarkan user_id"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                mp.id,
                m.bab,
                m.judul,
                m.filename,
                mp.is_watched,
                mp.is_completed,
                mp.watched_at,
                mp.completed_at
            FROM materi_progress mp
            JOIN materi m ON mp.materi_id = m.id
            WHERE mp.user_id = %s
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()

        cursor.close()
        conn.close()
        return data
