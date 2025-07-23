import random
from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('Map', description='Peta dan Progres Pengguna')

# ====== SCHEMA =======
tile_model = api.model('Tile', {
    'id': fields.Integer,
    'level_id': fields.Integer,
    'position': fields.Integer,
    'type': fields.String,
    'icon': fields.String,
    'status': fields.String
})

level_model = api.model('Level', {
    'id': fields.Integer,
    'name': fields.String,
    'theme': fields.String,
    'background_image': fields.String,
    'lives': fields.Integer,  # tambahan lives per level
    'tiles': fields.List(fields.Nested(tile_model))
})


# ====== ENDPOINT =======
@api.route('/')
class MapList(Resource):
    @api.doc(params={'user_id': 'ID pengguna (default: 9)'})
    @api.marshal_list_with(level_model)
    def get(self):
        """Ambil data map lengkap dengan progres user"""
        user_id = request.args.get('user_id', default=9, type=int)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Ambil semua level
        cursor.execute("SELECT * FROM levels")
        levels = cursor.fetchall()

        for level in levels:
            level_id = level['id']

            cursor.execute("""
                SELECT t.*, p.status AS progress_status
                FROM tiles t
                LEFT JOIN user_progress p ON t.id = p.tile_id AND p.user_id = %s
                WHERE t.level_id = %s
                ORDER BY t.position ASC
            """, (user_id, level_id))
            tiles = cursor.fetchall()

            # Mapping manual status
            for tile in tiles:
                tile_status = tile['progress_status']
                if tile_status == 'completed':
                    tile['status'] = 'completed'
                elif tile_status == 'in_progress':
                    tile['status'] = 'unlocked'
                elif tile_status == 'failed':
                    tile['status'] = 'failed'
                elif tile_status == 'unlocked':
                    tile['status'] = 'unlocked'
                else:
                    tile['status'] = 'locked'

                del tile['progress_status']  # bersihkan kolom sementara

            level['tiles'] = tiles
            cursor.execute("""
                SELECT lives
                FROM user_progress up
                JOIN tiles t ON up.tile_id = t.id
                WHERE up.user_id = %s AND t.level_id = %s
                      AND up.status IN ('unlocked', 'in_progress', 'failed')
                ORDER BY up.tile_id DESC
                LIMIT 1
            """, (user_id, level_id))
            result = cursor.fetchone()
            level['lives'] = result['lives'] if result else 3  # default 3
        cursor.close()
        conn.close()
        return levels


def fisher_yates_shuffle(arr):
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr
