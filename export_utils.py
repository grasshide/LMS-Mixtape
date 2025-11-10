import os
import shutil
import pathlib
import zipfile
import subprocess
from datetime import datetime
from config import EXPORT_DIR, PUID, PGID
from audio_utils import get_artist_and_title, embed_cover, copy_meatdata

def apply_permissions(path: pathlib.Path):
    """Apply PUID and PGID permissions to a file or directory if set"""
    if PUID is None or PGID is None:
        return  # Skip if PUID or PGID are not set

    try:
        path = pathlib.Path(path)  # ensure it's a Path object
        os.chown(path, int(PUID), int(PGID))

        # Set read/write permissions for owner and group
        if path.is_file():
            path.chmod(0o664)
        else:
            path.chmod(0o775)
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

def copy_songs(selected_songs, export_format='folder', embed_covers=True, rename_files=True, song_downsampling=False, sync_folder=False):
    """Copy selected songs to export directory"""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    
    if export_format == 'zip':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        if sync_folder:
            export_folder = os.path.join(EXPORT_DIR, "sync")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = os.path.join(EXPORT_DIR, f"music_export_{timestamp}")
        
        os.makedirs(export_folder, exist_ok=True)
        
        # Apply permissions to the export folder
        apply_permissions(export_folder)
        
        for song in selected_songs:
            source = pathlib.Path(song['url'])
            
            if not source.exists():
                continue
            
            # Create target filename
            target_filename = create_target_filename(source, song['filename'], rename_files)
            target_path = os.path.join(export_folder, target_filename)

            try:
                # only convert flac
                if song_downsampling and pathlib.Path(source).suffix.lower() == ".flac":

                    # Change file extension / overwrite target_path
                    base, _ = os.path.splitext(target_filename)
                    target_filename = base + '.mp3'
                    target_path = os.path.join(export_folder, target_filename)

                    # Start FLAC decoder (write PCM to stdout)
                    flac_proc = subprocess.Popen(
                        ["flac", "-dcs", "--", source],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                    )

                    # Start LAME encoder (read PCM from stdin)
                    lame_proc = subprocess.run(
                        ["lame", "-S", "-V", "0", "--vbr-new", "--add-id3v2", "--ignore-tag-errors", "-", target_path],
                        stdin=flac_proc.stdout,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )

                    # Close the FLAC process's stdout to signal EOF
                    flac_proc.stdout.close()
                    flac_proc.wait()

                    # Copy metadata
                    copy_meatdata(source, target_path)

                    # Delete the source if in place update
                    if os.path.dirname(source) == os.path.dirname(target_path):
                        # check if targes exists and is larger that 100Kb
                        if pathlib.Path(target_path).exists() and os.path.getsize(target_path) > 100000:
                            os.remove(source)
                else:
                    # Copy file
                    shutil.copy2(source, target_path)

                if embed_covers:
                    embed_cover(source, target_path)
                # Apply permissions to the copied file
                apply_permissions(target_path)
            except Exception as e:
                print(f"Error copying {source}: {e}")
        
        return export_folder 