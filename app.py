import os
from pathlib import Path
import io
from flask import Flask, render_template, request, jsonify, send_file, abort, Response
from PIL import Image, ImageOps
from config import SECRET_KEY, MAX_CONTENT_LENGTH, EXPORT_DIR, COVER_MAX_SIZE, COVER_QUALITY
from database import query_songs
from export_utils import copy_songs, create_target_filename
from audio_utils import extract_embedded_cover, get_audio_metadata

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
        rating = data.get('rating')
        limit = data.get('limit')
        exclude_genres = data.get('exclude_genres', [])
        dyn_ps_val = data.get('dyn_ps_val')
        album_limit = data.get('album_limit')
        order_by = data.get('order_by', 'added')
        added_before = data.get('added_before')
        
        songs = query_songs(rating, limit, exclude_genres, dyn_ps_val, album_limit, order_by, added_before)


        # Mark songs that already exist in the sync folder
        sync_dir = Path(EXPORT_DIR) / "sync"

        if sync_dir.is_dir():
            for song in songs:
                song['exists_in_sync'] = False
                try:
                    # Check renamed filename (default export behavior)
                    source_path = Path(song['url'])
                    renamed_filename = create_target_filename(source_path, song['filename'], rename_files=True)
                    renamed_path = sync_dir / renamed_filename

                    if renamed_path.is_file():
                        song['exists_in_sync'] = True

                    # Check original filename
                    original_path = sync_dir / song['filename']
                    if original_path.is_file():
                        song['exists_in_sync'] = True

                    # Additionally check for mp3 (if original file is not mp3)
                    if source_path.suffix.lower() != '.mp3':
                        base_name = Path(song['filename']).stem
                        renamed_base = Path(renamed_filename).stem

                        mp3_path = sync_dir / f"{base_name}.mp3"
                        renamed_mp3_path = sync_dir / f"{renamed_base}.mp3"

                        if mp3_path.is_file() or renamed_mp3_path.is_file():
                            song['exists_in_sync'] = True

                except Exception as e:
                    print(f"[ERROR] Checking file existence: {e}")
                
        else:
            for song in songs:
                song['exists_in_sync'] = False
        
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

@app.route('/api/sync/list', methods=['GET'])
def api_sync_list():
    """List audio files in the fixed sync folder"""
    try:
        sync_dir = os.path.join(EXPORT_DIR, "sync")
        if not os.path.isdir(sync_dir):
            return jsonify({'success': True, 'songs': [], 'count': 0})

        allowed_exts = {'.mp3', '.flac', '.wav', '.ogg', '.opus', '.aac'}
        items = []
        import urllib.parse
        for name in sorted(os.listdir(sync_dir)):
            path = os.path.join(sync_dir, name)
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_exts:
                continue
            
            # Extract metadata from audio file
            source_path = Path(path)
            metadata = get_audio_metadata(source_path)
            
            # Build a song-like object to reuse renderer
            url = path
            cover_url = f"/api/cover?path={urllib.parse.quote(url)}"
            filesize = round(os.path.getsize(path) / (1024 * 1024), 0);
            
            # Use extracted metadata if available, otherwise fall back to filename
            if metadata:
                title = metadata.get('title', '') or os.path.splitext(name)[0]
                artist = metadata.get('artist', '') or 'Unknown Artist'
                album = metadata.get('album', '') or 'Unknown Album'
                genre = metadata.get('genre', '') or ''
                year = metadata.get('year')
            else:
                # Fallback to filename-based values if metadata extraction fails
                title = os.path.splitext(name)[0]
                artist = 'Unknown Artist'
                album = 'Unknown Album'
                genre = ''
                year = None
            
            items.append({
                'url': url,
                'title': title,
                'artist': artist,
                'genre': genre,
                'rating': 0,
                'added': None,
                'last_played': None,
                'year': year,
                'album': album,
                'dyn_ps_val': None,
                'filename': name,
                'cover_url': cover_url,
                'filesize': filesize,
                'filetype': source_path.suffix.upper().lstrip('.')
            })

        return jsonify({'success': True, 'songs': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync/delete', methods=['POST'])
def api_sync_delete():
    """Delete a file from the fixed sync folder"""
    try:
        data = request.get_json() or {}
        filename = data.get('filename')
        if not filename:
            return jsonify({'success': False, 'error': 'Missing filename'}), 400

        sync_dir = os.path.join(EXPORT_DIR, "sync")
        target_path = os.path.abspath(os.path.join(sync_dir, filename))
        sync_dir_abs = os.path.abspath(sync_dir)

        # Safety: ensure target resides in sync directory
        if not target_path.startswith(sync_dir_abs + os.sep):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        if not os.path.isfile(target_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        os.remove(target_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """API endpoint to export selected songs"""
    try:
        data = request.get_json()
        selected_songs = data.get('songs', [])
        export_format = data.get('format', 'folder')
        embed_covers = data.get('embed_covers', True)
        rename_files = data.get('rename_files', True)
        song_downsampling = data.get('song_downsampling', False)
        sync_folder = data.get('sync_folder', False)
        
        if not selected_songs:
            return jsonify({
                'success': False,
                'error': 'No songs selected'
            }), 400
        
        result_path = copy_songs(selected_songs, export_format, embed_covers, rename_files, song_downsampling, sync_folder)
        
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
    song_path = Path(file_path)
    if not song_path.exists():
        abort(404, description='Song file not found')
    parent_dir = song_path.parent
    for cover_name in ["cover.jpg", "cover.png", "cover.jpeg", "folder.jpg", "folder.png", "folder.jpeg"]:
        cover_path = parent_dir / cover_name
        if cover_path.is_file():
            try:
                with Image.open(str(cover_path)) as img:
                    img = ImageOps.exif_transpose(img)
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")
                    img.thumbnail(COVER_MAX_SIZE, Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=COVER_QUALITY, optimize=True, progressive=True)
                    buf.seek(0)
                resp = Response(buf.getvalue(), mimetype='image/jpeg')
                resp.headers['Cache-Control'] = 'public, max-age=86400'
                return resp
            except Exception:
                # Fallback to sending the original if resize fails
                mimetype = 'image/png' if cover_name.endswith('.png') else 'image/jpeg'
                return send_file(str(cover_path), mimetype=mimetype)
    # Try extracting embedded cover from the audio file
    img_bytes, mime = extract_embedded_cover(song_path)
    if img_bytes and mime:
        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.thumbnail(COVER_MAX_SIZE, Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=COVER_QUALITY, optimize=True, progressive=True)
                buf.seek(0)
            resp = Response(buf.getvalue(), mimetype='image/jpeg')
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
        except Exception:
            return Response(img_bytes, mimetype=mime)
    # Fallback to default cover image
    default_cover = os.path.join('static', 'default-cover.png')
    return send_file(default_cover, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 