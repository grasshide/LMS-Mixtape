import os
import sqlite3
import urllib.parse
from config import LMS_DB_DIR

def get_db_connection():
    """Create a database connection to the LMS database"""
    persist_db = os.path.join(LMS_DB_DIR, 'prefs', 'persist.db')
    library_db = os.path.join(LMS_DB_DIR, 'cache', 'library.db')
    
    if not os.path.exists(persist_db) or not os.path.exists(library_db):
        raise FileNotFoundError("LMS database files not found")
    
    con = sqlite3.connect(persist_db)
    cur = con.cursor()
    cur.execute(f"ATTACH DATABASE '{library_db}' AS persist")
    return con

def query_songs(rating=40, limit=50, exclude_genres=None, dyn_ps_val=None, album_limit=None, randomize=False, added_before=None):
    """Query songs from the LMS database"""
    
    con = get_db_connection()
    cur = con.cursor()
    
    # Check if alternativeplaycount table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alternativeplaycount'")
    has_alternativeplaycount = cur.fetchone() is not None
    
    # Build common conditions and parameters
    base_conditions = ["audio = 1", "IFNULL(tracks_persistent.rating, 0) >= ?"]
    params = [rating]
    
    if exclude_genres is not None:
        placeholders = ','.join(['?' for _ in exclude_genres])
        base_conditions.append(f"genres.name NOT IN ({placeholders})")
        params.extend(exclude_genres)
    
    if dyn_ps_val is not None and dyn_ps_val != 0 and has_alternativeplaycount:
        base_conditions.append("IFNULL(alternativeplaycount.dynPSval, 0) > ?")
        params.append(dyn_ps_val)
    
    if added_before is not None:
        base_conditions.append("tracks.timestamp < ?")
        params.append(added_before)
    
    where_clause = " AND ".join(base_conditions)
    
    # Build query based on whether album limiting is enabled
    if album_limit is not None and album_limit > 0:
        # Use window function to limit tracks per album
        order_clause = "RANDOM()" if randomize else "tracks_persistent.added DESC"
        
        # Conditional JOIN for alternativeplaycount
        alternativeplaycount_join = "LEFT JOIN alternativeplaycount ON tracks.url = alternativeplaycount.url" if has_alternativeplaycount else ""
        dynpsval_select = "alternativeplaycount.dynPSval" if has_alternativeplaycount else "NULL as dynPSval"
        
        query = f'''
        WITH ranked_tracks AS (
            SELECT 
                tracks.url,
                tracks.title,
                contributors.name as artist,
                genres.name as genre,
                tracks_persistent.rating,
                tracks_persistent.added,
                albums.title as album_title,
                {dynpsval_select},
                ROW_NUMBER() OVER (PARTITION BY tracks.album ORDER BY {order_clause}) as album_rank
            FROM tracks
            JOIN tracks_persistent ON tracks.url = tracks_persistent.url
            JOIN genre_track ON tracks.id = genre_track.track
            JOIN genres ON genre_track.genre = genres.id
            JOIN contributor_track ON tracks.id = contributor_track.track
            JOIN contributors ON tracks.primary_artist = contributors.id
            JOIN albums on tracks.album=albums.id
            {alternativeplaycount_join}
            WHERE {where_clause}
        )
        SELECT 
            url,
            title,
            artist,
            genre,
            rating,
            added,
            album_title,
            dynPSval
        FROM ranked_tracks
        WHERE album_rank <= ?
        ORDER BY {'RANDOM()' if randomize else 'added DESC'}
        LIMIT ?;
        '''
        params.extend([album_limit, limit])
    else:
        # Original query without album limiting
        order_clause = "RANDOM()" if randomize else "tracks_persistent.added DESC"
        
        # Conditional JOIN for alternativeplaycount
        alternativeplaycount_join = "LEFT JOIN alternativeplaycount ON tracks.url = alternativeplaycount.url" if has_alternativeplaycount else ""
        dynpsval_select = "alternativeplaycount.dynPSval" if has_alternativeplaycount else "NULL as dynPSval"
        
        query = f'''
        SELECT 
            tracks.url,
            tracks.title,
            contributors.name as artist,
            genres.name as genre,
            tracks_persistent.rating,
            tracks_persistent.added,
            albums.title,
            {dynpsval_select}
        FROM tracks
        JOIN tracks_persistent ON tracks.url = tracks_persistent.url
        JOIN genre_track ON tracks.id = genre_track.track
        JOIN genres ON genre_track.genre = genres.id
        JOIN contributor_track ON tracks.id = contributor_track.track
        JOIN contributors ON tracks.primary_artist = contributors.id
        JOIN albums on tracks.album=albums.id
        {alternativeplaycount_join}
        WHERE {where_clause}
        GROUP BY tracks.id
        ORDER BY {order_clause}
        LIMIT ?;
        '''
        params.append(limit)
    
    result = cur.execute(query, params)
    
    songs = []
    for row in result:
        url = row[0].replace("file://", "")
        url = urllib.parse.unquote(url)
        
        # Add cover_url for frontend
        cover_url = f"/api/cover?path={urllib.parse.quote(url)}"
        
        songs.append({
            'url': url,
            'title': row[1],
            'artist': row[2],
            'genre': row[3],
            'rating': row[4],
            'added': row[5],
            'album': row[6],
            'dyn_ps_val': row[7],
            'filename': os.path.basename(url),
            'cover_url': cover_url
        })
    
    con.close()
    return songs 