from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('storytelling-progress', description='API untuk progress storytelling')

# Model untuk Swagger UI
progress_model = api.model('StorytellingProgress', {
    'id': fields.Integer(readonly=True),
    'user_id': fields.Integer(required=True),
    'storytelling_id': fields.Integer(required=True),
    'is_favorite': fields.Boolean,
    'is_watched': fields.Boolean,
    'progress_seconds': fields.Integer,
    'updated_at': fields.String
})

@api.route('/')
class ProgressList(Resource):
    @api.expect(progress_model)
    def post(self):
        """Menambahkan atau memperbarui progress storytelling"""
        data = request.json
        user_id = data['user_id']
        storytelling_id = data['storytelling_id']
        is_favorite = data.get('is_favorite', False)
        is_watched = data.get('is_watched', False)
        progress_seconds = data.get('progress_seconds', 0)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Cek apakah progress sudah ada
        cursor.execute("""
            SELECT id FROM storytelling_progress 
            WHERE user_id = %s AND storytelling_id = %s
        """, (user_id, storytelling_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE storytelling_progress 
                SET is_favorite = %s,
                    is_watched = %s,
                    progress_seconds = %s,
                    updated_at = NOW()
                WHERE user_id = %s AND storytelling_id = %s
            """, (is_favorite, is_watched, progress_seconds, user_id, storytelling_id))
        else:
            cursor.execute("""
                INSERT INTO storytelling_progress 
                (user_id, storytelling_id, is_favorite, is_watched, progress_seconds, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (user_id, storytelling_id, is_favorite, is_watched, progress_seconds))

        conn.commit()
        cursor.close()
        conn.close()

        return {'message': 'Progress storytelling berhasil disimpan'}, 200

@api.route('/<int:user_id>')
class ProgressByUser(Resource):
    @api.marshal_list_with(progress_model)
    def get(self, user_id):
        """Mendapatkan semua progress storytelling berdasarkan user_id"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM storytelling_progress WHERE user_id = %s", (user_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
