from flask_restx import Namespace, Resource, fields
from flask import request
from db import get_connection
import os
from werkzeug.utils import secure_filename
from datetime import datetime

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

api = Namespace('SoalCRUD', description='CRUD data soal (admin)')

soal_model = api.model('Soal', {
    'kumpulan_soal_id': fields.Integer,
    'pertanyaan': fields.String,
    'gambar': fields.String,
    'pilihan_a': fields.String,
    'pilihan_b': fields.String,
    'pilihan_c': fields.String,
    'pilihan_d': fields.String,
    'jawaban_benar': fields.String,
    'penjelasan': fields.String,
    'gambar_a': fields.String,
    'gambar_b': fields.String,
    'gambar_c': fields.String,
    'gambar_d': fields.String
})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, prefix=''):
    if file and allowed_file(file.filename):
        filename = secure_filename(
            f"{prefix}_{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return ''


@api.route('/kumpulan-soal')
class KumpulanSoalList(Resource):
    def get(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama FROM kumpulan_soal")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data


@api.route('/')
class SoalList(Resource):
    def get(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM soal")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    def post(self):
        data = request.form

        # Simpan file jika ada
        gambar = save_file(request.files.get('gambar')
                           ) if 'gambar' in request.files else ''
        gambar_a = save_file(request.files.get('gambar_a')
                             ) if 'gambar_a' in request.files else ''
        gambar_b = save_file(request.files.get('gambar_b')
                             ) if 'gambar_b' in request.files else ''
        gambar_c = save_file(request.files.get('gambar_c')
                             ) if 'gambar_c' in request.files else ''
        gambar_d = save_file(request.files.get('gambar_d')
                             ) if 'gambar_d' in request.files else ''

        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO soal (
                kumpulan_soal_id, pertanyaan, gambar, pilihan_a, pilihan_b, pilihan_c, pilihan_d,
                jawaban_benar, penjelasan, gambar_a, gambar_b, gambar_c, gambar_d, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(sql, (
            data['kumpulan_soal_id'],
            data['pertanyaan'],
            gambar,
            data['pilihan_a'],
            data['pilihan_b'],
            data['pilihan_c'],
            data['pilihan_d'],
            data['jawaban_benar'],
            data.get('penjelasan', ''),
            gambar_a,
            gambar_b,
            gambar_c,
            gambar_d
        ))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {'message': 'Soal berhasil ditambahkan', 'id': new_id}, 201


@api.route('/<int:id>')
@api.param('id', 'ID Soal')
class SoalItem(Resource):
    def get(self, id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM soal WHERE id = %s", (id,))
        soal = cursor.fetchone()
        cursor.close()
        conn.close()
        if soal:
            return soal
        api.abort(404, "Soal tidak ditemukan")

    def put(self, id):
        data = request.form

        # Handle penghapusan file jika checkbox diaktifkan
        def handle_gambar(field):
            if f'hapus_{field}' in data:
                return ''  # kosongkan jika ingin dihapus
            else:
                return save_file(request.files.get(field)) or data.get(f'{field}_lama', '')

        gambar = handle_gambar('gambar')
        gambar_a = handle_gambar('gambar_a')
        gambar_b = handle_gambar('gambar_b')
        gambar_c = handle_gambar('gambar_c')
        gambar_d = handle_gambar('gambar_d')

        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE soal SET kumpulan_soal_id=%s, pertanyaan=%s, gambar=%s, pilihan_a=%s, pilihan_b=%s,
            pilihan_c=%s, pilihan_d=%s, jawaban_benar=%s, penjelasan=%s,
            gambar_a=%s, gambar_b=%s, gambar_c=%s, gambar_d=%s, updated_at=NOW()
            WHERE id = %s
        """
        cursor.execute(sql, (
            data['kumpulan_soal_id'],
            data['pertanyaan'],
            gambar,
            data['pilihan_a'],
            data['pilihan_b'],
            data['pilihan_c'],
            data['pilihan_d'],
            data['jawaban_benar'],
            data.get('penjelasan', ''),
            gambar_a,
            gambar_b,
            gambar_c,
            gambar_d,
            id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return {'message': 'Soal berhasil diperbarui'}

    def delete(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM soal WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'message': 'Soal berhasil dihapus'}
