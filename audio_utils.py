import os
import pathlib
import base64
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, ID3NoHeaderError

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

def get_audio_metadata(source_file):
    """Extract comprehensive metadata from music file tags.
    
    Returns a dict with: artist, title, album, year, genre, or None if extraction fails.
    """
    try:
        tags = None
        if source_file.suffix == '.mp3':
            tags = EasyID3(str(source_file))
        elif source_file.suffix == '.flac':
            tags = FLAC(str(source_file))

        
        if tags:
            metadata = {}
            # Extract common fields
            if hasattr(tags, 'get'):
                # EasyID3 or FLAC style
                metadata['artist'] = tags.get("artist", [""])[0] if "artist" in tags else ""
                metadata['title'] = tags.get("title", [""])[0] if "title" in tags else ""
                metadata['album'] = tags.get("album", [""])[0] if "album" in tags else ""
                metadata['genre'] = tags.get("genre", [""])[0] if "genre" in tags else ""
                
                # Year/date handling
                year = None
                if "date" in tags:
                    date_str = tags.get("date", [""])[0]
                    if date_str:
                        # Extract year from date string (could be "2023" or "2023-01-01")
                        try:
                            year = int(date_str.split('-')[0])
                        except (ValueError, AttributeError):
                            pass
                elif "originaldate" in tags:
                    date_str = tags.get("originaldate", [""])[0]
                    if date_str:
                        try:
                            year = int(date_str.split('-')[0])
                        except (ValueError, AttributeError):
                            pass
                metadata['year'] = year
            else:
                return None
            
            return metadata
    except Exception as e:
        print(f"Error reading metadata from {source_file}: {e}")
    
    return None

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
    file_path = pathlib.Path(file_path)
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

def extract_embedded_cover(file_path):
    """Extract embedded cover image bytes and mimetype from a music file.

    Returns a tuple of (image_bytes, mimetype) or (None, None) if not found.
    """
    try:
        if file_path.suffix == '.mp3':
            audio = MP3(file_path, ID3=ID3)
            if audio.tags:
                # Prefer direct APIC frames if available
                try:
                    apic_frames = audio.tags.getall('APIC')  # type: ignore[attr-defined]
                except Exception:
                    apic_frames = []
                if apic_frames:
                    apic = apic_frames[0]
                    mime = getattr(apic, 'mime', None) or 'image/jpeg'
                    data = getattr(apic, 'data', None)
                    if data:
                        return data, mime
                # Fallback: iterate over tag values and find an APIC instance
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        mime = tag.mime or 'image/jpeg'
                        return tag.data, mime
        elif file_path.suffix == '.flac':
            flac = FLAC(file_path)
            # First try embedded pictures list
            if hasattr(flac, 'pictures') and flac.pictures:
                pic = flac.pictures[0]
                mime = getattr(pic, 'mime', None) or 'image/jpeg'
                return pic.data, mime
            # Then try VorbisComment tags with common fields
            if flac.tags:
                if 'coverart' in flac.tags and flac.tags['coverart']:
                    data_b64 = flac.tags['coverart'][0]
                    try:
                        img_bytes = base64.b64decode(data_b64)
                        return img_bytes, 'image/jpeg'
                    except Exception:
                        pass
                if 'metadata_block_picture' in flac.tags and flac.tags['metadata_block_picture']:
                    try:
                        data_b64 = flac.tags['metadata_block_picture'][0]
                        pic = Picture()
                        pic.parse(base64.b64decode(data_b64))
                        mime = getattr(pic, 'mime', None) or 'image/jpeg'
                        return pic.data, mime
                    except Exception:
                        pass
    except Exception as e:
        print(f"Error extracting embedded cover from {file_path}: {e}")
    return None, None

def copy_meatdata(source, target):
    """copy metadata as well as the cover (if present) from flac to mp3
    """
    # Read tags and cover art from the FLAC file
    flac_tags = FLAC(source)

    # Write tags to the new MP3 file
    mp3 = EasyID3(target)

    # Only copy keys that EasyID3 supports
    valid_keys = set(EasyID3.valid_keys.keys())
    for key, value in flac_tags.tags.items():
        key_lower = key.lower()
        if key_lower in valid_keys:
            mp3[key_lower] = value
    mp3.save()

    # Add cover art (if present)
    try:
        mp3_id3 = ID3(target)
    except ID3NoHeaderError:
        mp3_id3 = ID3()

    for picture in flac_tags.pictures:
        mp3_id3.add(APIC(
            encoding=3,       # UTF-8
            mime=picture.mime,
            type=3,           # Cover (front)
            desc="Cover",
            data=picture.data
        ))
    mp3_id3.save()


def embed_cover(source_path, target):
    """Embed cover art into music file if no cover is already embedded"""
    target = pathlib.Path(target)
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
        if target.suffix == '.mp3':
            add_mp3_cover(target, str(cover))
        elif target.suffix == '.flac':
            add_flac_cover(target, str(cover))
    except Exception as e:
        print(f"Error embedding cover: {e}") 