from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('achievement', description='Achievement Progress Management')

achievement_progress_model = api.model('AchievementProgress', {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'achievement_id': fields.Integer,
    'current_value': fields.Integer,
    'is_unlocked': fields.Boolean,
    'unlocked_at': fields.String,
    'title': fields.String,
    'description': fields.String,
    'icon_url': fields.String,
    'condition_type': fields.String,
    'condition_value': fields.Integer,
})

@api.route('/progress/<int:user_id>')
class AchievementProgressList(Resource):
    @api.marshal_list_with(achievement_progress_model)
    def get(self, user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    ap.*, 
                    am.title, am.description, am.icon_url, 
                    am.condition_type, am.condition_value
                FROM achievement_progress ap
                JOIN achievement_master am ON ap.achievement_id = am.id
                WHERE ap.user_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()
            return result, 200
        except Exception as e:
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
