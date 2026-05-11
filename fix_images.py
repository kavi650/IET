
"""Fix double extensions (.jpg.jpg -> .jpg) in static/images."""
import os

IMG_DIR = r"d:\Teslead\static\images"

for filename in os.listdir(IMG_DIR):
    if filename.endswith('.jpg.jpg'):
        old = os.path.join(IMG_DIR, filename)
        new = os.path.join(IMG_DIR, filename.replace('.jpg.jpg', '.jpg'))
        if not os.path.exists(new):
            os.rename(old, new)
            print(f"✅ {filename} → {filename.replace('.jpg.jpg', '.jpg')}")
        else:
            print(f"⚠️ Skipped {filename} (target already exists)")
    elif filename.endswith('.jpg.png'):
        old = os.path.join(IMG_DIR, filename)
        os.remove(old)
        print(f"🗑️ Removed duplicate: {filename}")

print("\nDone! Files fixed.")
