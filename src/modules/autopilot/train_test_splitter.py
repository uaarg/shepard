import zipfile
import os
import glob
import shutil
from sklearn.model_selection import train_test_split

zip_files = ['run1.zip', 'run2.zip', 'run3.zip', 'run4.zip', 'run5.zip', 'run6.zip']
extracted_dir = 'all_data'

os.makedirs(extracted_dir, exist_ok=True)

# Extract all zip files
for zip_file in zip_files:
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extracted_dir)
        
# Recursively find all images and labels
images = glob.glob(os.path.join(extracted_dir, '**', '*.jpeg'), recursive=True)
labels = glob.glob(os.path.join(extracted_dir, '**', '*.label'), recursive=True)

print(f"Found {len(images)} images and {len(labels)} labels")

# Split into train and test
train_images, test_images = train_test_split(images, test_size=0.2, random_state=42)

# Create folders
folders = ["dataset/images/train", "dataset/images/val", 
           "dataset/labels/train", "dataset/labels/val"]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Function to move images and corresponding labels
def move_files(file_list, img_dest, lbl_dest):
    for img_path in file_list:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        lbl_path = glob.glob(os.path.join(extracted_dir, '**', f"{base_name}.label"), recursive=True)
        shutil.copy(img_path, img_dest)
        if lbl_path:
            shutil.copy(lbl_path[0], lbl_dest)

# Copy train
move_files(train_images, "dataset/images/train", "dataset/labels/train")
# Copy test/val
move_files(test_images, "dataset/images/val", "dataset/labels/val")
