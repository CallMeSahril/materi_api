from flask import request, send_from_directory
from flask_restx import Namespace, Resource, fields
from db import get_connection
from config import UPLOAD_FOLDER
import mysql.connector

achievement_ns = Namespace('user', description='User Achievement Routes')

# Detail pencapaian per tile
achievement_detail_model = achievement_ns.model('AchievementDetail', {
    'tile_id': fields.Integer,
    'achievement_name': fields.String,
    'gambar': fields.String,
    'created_at': fields.String,
})

# Data response gabungan user + semua pencapaiannya
achievement_response_model = achievement_ns.model('AchievementResponse', {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'achievement': fields.List(fields.Nested(achievement_detail_model))
})


@achievement_ns.route('/achievements/<int:user_id>')
class UserAchievementList(Resource):
    @achievement_ns.marshal_with(achievement_response_model)
    def get(self, user_id):
        """Ambil profil user dan semua pencapaiannya"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Ambil data user
            cursor.execute(
                "SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return {'message': 'User not found'}, 404

            # Ambil semua pencapaian user
            cursor.execute("""
                SELECT tile_id, achievement_name, gambar, created_at
                FROM user_achievement
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            achievements = cursor.fetchall()

            return {
                'id': user['id'],
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'achievement': achievements
            }, 200

        except mysql.connector.Error as e:
            return {'message': f'Database error: {str(e)}'}, 500

        finally:
            cursor.close()
            conn.close()
