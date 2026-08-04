"""Helper script to migrate files for the Milestone 3 restructuring."""
import os
import shutil

BACKEND_DIR = os.path.dirname(__file__)

# 1. Copy joblib models to ml_models/
src_models = os.path.join(BACKEND_DIR, "models")
dst_models = os.path.join(BACKEND_DIR, "ml_models")
os.makedirs(dst_models, exist_ok=True)

for f in os.listdir(src_models):
    if f.endswith(".joblib"):
        src = os.path.join(src_models, f)
        dst = os.path.join(dst_models, f)
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")

# 2. Copy train_models.py to scripts/
scripts_dir = os.path.join(BACKEND_DIR, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
src_train = os.path.join(BACKEND_DIR, "train_models.py")
dst_train = os.path.join(scripts_dir, "train_models.py")
if os.path.exists(src_train):
    shutil.copy2(src_train, dst_train)
    print(f"Copied {src_train} -> {dst_train}")

print("\nMigration complete!")
print(f"ml_models contents: {os.listdir(dst_models)}")
print(f"scripts contents: {os.listdir(scripts_dir)}")
