import os
import datetime

folder = 'folder'
os.makedirs(folder, exist_ok=True)

for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)

    if not os.path.isdir(file_path):
        continue
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    new_filename = f"renamed {name}"

    target_path = os.path.join(folder, new_filename)

    try:
        os.rename(file_path, target_path)
        print(f"Renamed '{filename}' to '{new_filename}'")
    except Exception as e:
        print(f"Error renaming '{filename}': {e}")

