import random
from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace('Map', description='Peta dan Progres Pengguna')
add_life_by_id_model = api.model('AddLifeByUserId', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'amount': fields.Integer(required=True, description='Jumlah nyawa yang akan ditambahkan')
})

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


@api.route('/add-life')
class AddLife(Resource):
    @api.expect(add_life_by_id_model)
    def post(self):
        """Tambah nyawa ke user_progress terakhir user, maksimal 3"""
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount', 1)

        if not user_id:
            return {'message': 'user_id is required'}, 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Ambil entri terbaru user_progress user ini
        cursor.execute("""
            SELECT up.*
            FROM user_progress up
            INNER JOIN (
                SELECT user_id, MAX(updated_at) AS max_updated
                FROM user_progress
                WHERE user_id = %s
                GROUP BY user_id
            ) latest
            ON up.user_id = latest.user_id AND up.updated_at = latest.max_updated
            ORDER BY up.updated_at DESC
            LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return {'message': 'No user_progress record found for this user'}, 404

        # Tambahkan nyawa dengan batas maksimal 3
        current_lives = row['lives']
        added = min(amount, 3 - current_lives)
        new_lives = min(current_lives + amount, 3)

        if added <= 0:
            cursor.close()
            conn.close()
            return {
                'message': 'Lives already full (max 3)',
                'current_lives': current_lives
            }, 200

        cursor.execute("""
            UPDATE user_progress
            SET lives = %s
            WHERE id = %s
        """, (new_lives, row['id']))

        conn.commit()
        cursor.close()
        conn.close()

        return {
            'message': f"{added} lives added (max 3)",
            'tile_id': row['tile_id'],
            'new_lives': new_lives
        }, 200
