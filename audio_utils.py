import os
import pathlib
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

def get_artist_and_title(source_file):
    """Extract artist and title from music file tags"""
    try:
        tags = None
        if source_file.suffix == '.mp3':
            tags = EasyID3(str(source_file))
        elif source_file.suffix == '.flac':
            tags = FLAC(str(source_file))
        
        if tags:
            artist = tags.get("artist", [""])[0] if "artist" in tags else ""
            title = tags.get("title", [""])[0] if "title" in tags else ""
            return artist, title
    except Exception as e:
        print(f"Error reading tags from {source_file}: {e}")
    
    return None, None

def add_mp3_cover(filename, album_art):
    """Add cover art to MP3 file"""
    try:
        audio = MP3(filename, ID3=ID3)
        
        try:
            audio.add_tags()
        except error:
            pass
        
        if album_art.endswith('png'):
            mime = 'image/png'
        else:
            mime = 'image/jpeg'
        
        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc=u'Cover',
                data=open(album_art, 'rb').read()
            )
        )
        audio.save()
    except Exception as e:
        print(f"Error adding MP3 cover: {e}")

def add_flac_cover(filename, album_art):
    """Add cover art to FLAC file"""
    try:
        from mutagen.flac import Picture
        audio = File(filename)
        image = Picture()
        image.type = 3
        
        if album_art.endswith('png'):
            image.mime = 'image/png'
        else:
            image.mime = 'image/jpeg'
        image.desc = 'front cover'
        
        with open(album_art, 'rb') as f:
            image.data = f.read()
        
        audio.add_picture(image)
        audio.save()
    except Exception as e:
        print(f"Error adding FLAC cover: {e}")

def has_embedded_cover(file_path):
    """Check if a music file already has embedded cover art"""
    try:
        if file_path.suffix == '.mp3':
            audio = MP3(file_path, ID3=ID3)
            if audio.tags:
                for key in audio.tags.keys():
                    if key.startswith('APIC:'):
                        return True
        elif file_path.suffix == '.flac':
            audio = FLAC(file_path)
            # Check for VorbisComment metadata with COVERART or METADATA_BLOCK_PICTURE
            if audio.tags:
                # Check for COVERART field
                if 'coverart' in audio.tags:
                    return True
                # Check for METADATA_BLOCK_PICTURE (base64 encoded)
                if 'metadata_block_picture' in audio.tags:
                    return True
            # Also check for embedded pictures using the pictures property
            if hasattr(audio, 'pictures') and audio.pictures:
                return len(audio.pictures) > 0
    except Exception as e:
        print(f"Error checking embedded cover in {file_path}: {e}")
    return False

def embed_cover(source_path, target):
    """Embed cover art into music file if no cover is already embedded"""
    # Check if target file already has embedded cover
    if has_embedded_cover(target):
        return  # Skip if cover is already embedded
    
    cover = None
    
    # Look for cover files in the same directory
    parent_dir = source_path.parent
    for cover_name in ["cover.jpg", "cover.png", "cover.jpeg"]:
        cover_path = parent_dir / cover_name
        if cover_path.is_file():
            cover = cover_path
            break
    
    if cover is None:
        return
    
    try:
        if source_path.suffix == '.mp3':
            add_mp3_cover(target, str(cover))
        elif source_path.suffix == '.flac':
            add_flac_cover(target, str(cover))
    except Exception as e:
        print(f"Error embedding cover: {e}") 