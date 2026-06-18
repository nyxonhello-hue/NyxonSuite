import os
import shutil

box = "folder"

os.makedirs(box, exist_ok=True)

folders = {
    '.mp3': 'MP3',
    '.mp4': 'MP4',
    '.pdf': 'PDF',
    '.docx': 'DOCUMENTS',
    '.zip': 'ZIPS',
    '.py': 'CODE',
    '.html': 'CODE',
}

for folder_name in set(folders.values()):
    os.makedirs(os.path.join(box, folder_name), exist_ok=True)

# Organize files in the box directory
for filename in os.listdir(box):
    file_path = os.path.join(box, filename)
    
    # Skip if not a regular file (skip dirs, symlinks etc.)
    if not os.path.isfile(file_path):
        continue
    
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    if ext in folders:
        target_folder = folders[ext]
        target_path = os.path.join(box, target_folder, filename)
        
        try:
            shutil.move(file_path, target_path)
            print(f"Moved '{filename}' to '{target_folder}/'")
        except Exception as e:
            print(f"Error moving '{filename}': {e}")
    else:
        print(f"Skipping '{filename}' (no matching extension)")

