from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('storytelling-progress', description='Gabungan materi storytelling dan progress user')

# Model gabungan Story + Progress
story_progress_model = api.model('StoryProgressCombined', {
    'id': fields.Integer,  # storytelling.id
    'title': fields.String,
    'description': fields.String,
    'video_url': fields.String,
    'thumbnail_url': fields.String,
    'is_favorite': fields.Boolean,
    'is_watched': fields.Boolean,
    'progress_seconds': fields.Integer,
})

@api.route('/<int:user_id>')
class StoryProgressList(Resource):
    @api.marshal_list_with(story_progress_model)
    def get(self, user_id):
        """Mengambil semua materi storytelling beserta progress user (jika ada)"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            s.id,
            s.title,
            s.description,
            s.video_url,
            s.thumbnail_url,
            IFNULL(p.is_favorite, FALSE) AS is_favorite,
            IFNULL(p.is_watched, FALSE) AS is_watched,
            IFNULL(p.progress_seconds, 0) AS progress_seconds
        FROM storytelling s
        LEFT JOIN storytelling_progress p 
            ON s.id = p.storytelling_id AND p.user_id = %s
        ORDER BY s.id
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return results
