"""
Download a small sample dataset for quick training demonstration.
This script downloads a few sample face images from a public source.
"""

import os
import urllib.request
from pathlib import Path
import zipfile
import csv

SAMPLE_DATA_URL = "https://github.com/Artemis-TS-2/Face-Recognition-Dataset/raw/master/Selected%20Faces.zip"


def download_sample_dataset(output_dir: Path):
    """Download a small sample dataset for training demonstration."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = output_dir / "sample_faces.zip"
    images_dir = output_dir / "images"
    
    print("Downloading sample face images...")
    try:
        urllib.request.urlretrieve(SAMPLE_DATA_URL, zip_path)
        print(f"Downloaded to {zip_path}")
        
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        print("Organizing images...")
        images_dir.mkdir(exist_ok=True)
        
        # Find and copy all images
        image_extensions = ['.jpg', '.jpeg', '.png']
        all_images = []
        
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    src_path = Path(root) / file
                    if src_path != zip_path:
                        all_images.append(src_path)
        
        print(f"Found {len(all_images)} images")
        
        # Copy images to images directory
        for idx, img_path in enumerate(all_images[:100]):  # Limit to 100 images
            ext = img_path.suffix
            dest_path = images_dir / f"sample_{idx}{ext}"
            import shutil
            shutil.copy2(img_path, dest_path)
        
        # Clean up extracted files
        print("Cleaning up...")
        for item in output_dir.iterdir():
            if item != images_dir and item != zip_path and item.is_dir():
                import shutil
                shutil.rmtree(item)
        
        zip_path.unlink()
        
        print(f"\nSample dataset ready!")
        print(f"Images saved to: {images_dir}")
        print(f"Total images: {len(list(images_dir.glob('*.*')))}")
        print(f"\nNext step: Create labels with:")
        print(f"  python datasets/create_sample_dataset.py --images-dir {images_dir} --output datasets/sample")
        
    except Exception as e:
        print(f"Error downloading sample dataset: {e}")
        print("\nAlternative: Use your own images with:")
        print(f"  python datasets/create_sample_dataset.py --images-dir /path/to/your/images --output datasets/sample")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download sample face images for training")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/raw/sample"),
        help="Output directory for downloaded images"
    )
    
    args = parser.parse_args()
    
    download_sample_dataset(args.output)
