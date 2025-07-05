import os
import pathlib
from flask import Flask, render_template, request, jsonify, send_file, abort
from config import SECRET_KEY, MAX_CONTENT_LENGTH, EXPORT_DIR
from database import query_songs
from export_utils import copy_songs

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint to query songs"""
    try:
        data = request.get_json()
        rating = data.get('rating', 40)
        limit = data.get('limit', 50)
        exclude_genres = data.get('exclude_genres', [])
        dyn_ps_val = data.get('dyn_ps_val')
        album_limit = data.get('album_limit')
        randomize = data.get('randomize', False)
        added_after = data.get('added_after')
        
        songs = query_songs(rating, limit, exclude_genres, dyn_ps_val, album_limit, randomize, added_after)
        
        return jsonify({
            'success': True,
            'songs': songs,
            'count': len(songs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """API endpoint to export selected songs"""
    try:
        data = request.get_json()
        selected_songs = data.get('songs', [])
        export_format = data.get('format', 'folder')
        embed_covers = data.get('embed_covers', True)
        rename_files = data.get('rename_files', True)
        
        if not selected_songs:
            return jsonify({
                'success': False,
                'error': 'No songs selected'
            }), 400
        
        result_path = copy_songs(selected_songs, export_format, embed_covers, rename_files)
        
        return jsonify({
            'success': True,
            'export_path': result_path,
            'format': export_format
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download exported files"""
    try:
        file_path = os.path.join(EXPORT_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cover')
def api_cover():
    """Serve album cover image for a given song file path (query param: path)"""
    file_path = request.args.get('path')
    if not file_path:
        abort(400, description='Missing path parameter')
    song_path = pathlib.Path(file_path)
    if not song_path.exists():
        abort(404, description='Song file not found')
    parent_dir = song_path.parent
    for cover_name in ["cover.jpg", "cover.png", "cover.jpeg", "folder.jpg", "folder.png", "folder.jpeg"]:
        cover_path = parent_dir / cover_name
        if cover_path.is_file():
            # Guess mimetype
            if cover_name.endswith('.png'):
                mimetype = 'image/png'
            else:
                mimetype = 'image/jpeg'
            return send_file(str(cover_path), mimetype=mimetype)
    abort(404, description='Cover image not found')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 