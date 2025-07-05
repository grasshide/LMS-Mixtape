import os
import shutil
import pathlib
import zipfile
from datetime import datetime
from config import EXPORT_DIR, PUID, PGID
from audio_utils import get_artist_and_title, embed_cover

def apply_permissions(path):
    """Apply PUID and PGID permissions to a file or directory if set"""
    if PUID is None or PGID is None:
        return  # Skip if PUID or PGID are not set
    
    try:
        os.chown(path, int(PUID), int(PGID))
        # Set read/write permissions for owner and group
        os.chmod(path, 0o664 if os.path.isfile(path) else 0o775)
    except Exception as e:
        print(f"Error applying permissions to {path}: {e}")

def create_target_filename(source_path, original_filename, rename_files=True):
    """Create target filename based on source file and rename preference"""
    if not rename_files:
        return original_filename
    
    # Get artist and title from tags
    artist, title = get_artist_and_title(source_path)
    
    # Create filename
    if artist and title:
        target_filename = f"{artist} - {title}{source_path.suffix}"
    else:
        target_filename = original_filename
    
    # Clean filename
    target_filename = "".join(c for c in target_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
    
    return target_filename

def copy_songs(selected_songs, export_format='folder', embed_covers=True, rename_files=True):
    """Copy selected songs to export directory"""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export_format == 'zip':
        zip_filename = f"music_export_{timestamp}.zip"
        zip_path = os.path.join(EXPORT_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for song in selected_songs:
                source = pathlib.Path(song['url'])
                
                if not source.exists():
                    continue
                
                # Create target filename
                target_filename = create_target_filename(source, song['filename'], rename_files)
                
                # Add to zip
                zipf.write(source, target_filename)
        
        return zip_path
    else:
        # Export to folder
        export_folder = os.path.join(EXPORT_DIR, f"music_export_{timestamp}")
        os.makedirs(export_folder, exist_ok=True)
        
        # Apply permissions to the export folder
        apply_permissions(export_folder)
        
        copied_files = []
        for song in selected_songs:
            source = pathlib.Path(song['url'])
            
            if not source.exists():
                continue
            
            # Create target filename
            target_filename = create_target_filename(source, song['filename'], rename_files)
            target_path = os.path.join(export_folder, target_filename)
            
            # Copy file
            try:
                shutil.copy2(source, target_path)
                if embed_covers:
                    embed_cover(source, target_path)
                # Apply permissions to the copied file
                apply_permissions(target_path)
                copied_files.append(target_filename)
            except Exception as e:
                print(f"Error copying {source}: {e}")
        
        return export_folder 