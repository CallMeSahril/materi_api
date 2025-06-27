from flask import request, send_from_directory
from flask_restx import Namespace, Resource, fields
from db import get_connection
from config import UPLOAD_FOLDER

api = Namespace(
    'storytelling', description='API untuk materi video storytelling')

story_model = api.model('Story', {
    'id': fields.Integer(readonly=True),
    'title': fields.String(required=True),
    'description': fields.String,
    'video_url': fields.String,
    'thumbnail_url': fields.String,
    'is_favorite': fields.Boolean(default=False),
})


@api.route('/')
class StoryList(Resource):
    @api.marshal_list_with(story_model)
    def get(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM storytelling")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    @api.expect(story_model)
    def post(self):
        data = request.json
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO storytelling (title, description, video_url, thumbnail_url, is_favorite)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['title'],
            data.get('description', ''),
            data.get('video_url', ''),
            data.get('thumbnail_url', ''),
            data.get('is_favorite', False)
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return {'message': 'Story berhasil ditambahkan'}, 201


@api.route('/<int:id>')
class Story(Resource):
    @api.expect(story_model)
    def put(self, id):
        data = request.json
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE storytelling
            SET title=%s, description=%s, video_url=%s, thumbnail_url=%s, is_favorite=%s
            WHERE id=%s
        """, (
            data['title'],
            data.get('description', ''),
            data.get('video_url', ''),
            data.get('thumbnail_url', ''),
            data.get('is_favorite', False),
            id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return {'message': 'Story berhasil diperbarui'}

    def delete(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM storytelling WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'message': 'Story berhasil dihapus'}
