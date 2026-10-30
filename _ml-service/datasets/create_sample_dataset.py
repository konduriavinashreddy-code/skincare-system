"""
Create a sample dataset for testing/training without requiring Kaggle download.
This script can create synthetic labels for any folder of face images.
"""

import os
import csv
import random
from pathlib import Path
from typing import List

OBSERVATIONS = ["acne_like_features", "redness", "dark_spots", "oiliness", "dryness", "uneven_tone", "texture", "fine_lines"]
SKIN_TYPES = ["normal", "dry", "oily", "combination"]


def create_sample_dataset(
    images_dir: Path,
    output_dir: Path,
    train_split: float = 0.8,
    val_split: float = 0.1
):
    """
    Create a sample dataset from a folder of images.
    Assigns random but plausible labels for testing purposes.
    
    Args:
        images_dir: Directory containing face images
        output_dir: Output directory for CSV files
        train_split: Fraction for training
        val_split: Fraction for validation
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all images
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    images = []
    for ext in image_extensions:
        images.extend(images_dir.glob(f"*{ext}"))
        images.extend(images_dir.glob(f"*{ext.upper()}"))
    
    if not images:
        print(f"ERROR: No images found in {images_dir}")
        print("Please ensure the directory contains image files (jpg, png, webp)")
        return
    
    print(f"Found {len(images)} images")
    
    # Shuffle and split
    random.shuffle(images)
    n_total = len(images)
    n_train = int(n_total * train_split)
    n_val = int(n_total * val_split)
    
    train_images = images[:n_train]
    val_images = images[n_train:n_train + n_val]
    test_images = images[n_train + n_val:]
    
    print(f"Train: {len(train_images)}, Val: {len(val_images)}, Test: {len(test_images)}")
    
    # Create labels for each split
    for split_name, split_images in [('train', train_images), ('val', val_images), ('test', test_images)]:
        csv_path = output_dir / f"{split_name}_labels.csv"
        
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            header = ['image'] + OBSERVATIONS + ['skin_type']
            writer.writerow(header)
            
            for img_path in split_images:
                # Use relative path from images_dir
                relative_path = img_path.relative_to(images_dir)
                
                # Generate random but plausible labels
                skin_type = random.choice(SKIN_TYPES)
                
                # Generate observation scores based on skin type
                if skin_type == "oily":
                    obs_scores = {
                        "acne_like_features": random.uniform(0.3, 0.7),
                        "redness": random.uniform(0.2, 0.5),
                        "dark_spots": random.uniform(0.2, 0.4),
                        "oiliness": random.uniform(0.7, 0.95),
                        "dryness": random.uniform(0.05, 0.2),
                        "uneven_tone": random.uniform(0.3, 0.5),
                        "texture": random.uniform(0.3, 0.5),
                        "fine_lines": random.uniform(0.1, 0.3)
                    }
                elif skin_type == "dry":
                    obs_scores = {
                        "acne_like_features": random.uniform(0.1, 0.3),
                        "redness": random.uniform(0.3, 0.5),
                        "dark_spots": random.uniform(0.2, 0.4),
                        "oiliness": random.uniform(0.05, 0.2),
                        "dryness": random.uniform(0.7, 0.95),
                        "uneven_tone": random.uniform(0.4, 0.6),
                        "texture": random.uniform(0.5, 0.7),
                        "fine_lines": random.uniform(0.4, 0.6)
                    }
                elif skin_type == "combination":
                    obs_scores = {
                        "acne_like_features": random.uniform(0.2, 0.5),
                        "redness": random.uniform(0.2, 0.4),
                        "dark_spots": random.uniform(0.2, 0.4),
                        "oiliness": random.uniform(0.4, 0.7),
                        "dryness": random.uniform(0.3, 0.5),
                        "uneven_tone": random.uniform(0.3, 0.5),
                        "texture": random.uniform(0.3, 0.5),
                        "fine_lines": random.uniform(0.2, 0.4)
                    }
                else:  # normal
                    obs_scores = {
                        "acne_like_features": random.uniform(0.05, 0.2),
                        "redness": random.uniform(0.1, 0.3),
                        "dark_spots": random.uniform(0.1, 0.3),
                        "oiliness": random.uniform(0.3, 0.5),
                        "dryness": random.uniform(0.2, 0.4),
                        "uneven_tone": random.uniform(0.1, 0.3),
                        "texture": random.uniform(0.1, 0.3),
                        "fine_lines": random.uniform(0.1, 0.3)
                    }
                
                # Write row
                row = [str(relative_path)] + [obs_scores[obs] for obs in OBSERVATIONS] + [skin_type]
                writer.writerow(row)
        
        print(f"Created {csv_path} with {len(split_images)} samples")
    
    print(f"\nDataset preparation complete!")
    print(f"CSV files saved to: {output_dir}")
    print(f"\nIMPORTANT: The image paths in CSV are relative to: {images_dir}")
    print(f"To train, run:")
    print(f"  python training/train.py --csv {output_dir / 'train_labels.csv'} --val-csv {output_dir / 'val_labels.csv'} --output models/skin_model.pt --epochs 20")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create sample dataset from a folder of images for testing"
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        required=True,
        help="Directory containing face images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/sample"),
        help="Output directory for CSV files"
    )
    parser.add_argument(
        "--train-split",
        type=float,
        default=0.8,
        help="Training split fraction (default: 0.8)"
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.1,
        help="Validation split fraction (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    create_sample_dataset(
        images_dir=args.images_dir,
        output_dir=args.output,
        train_split=args.train_split,
        val_split=args.val_split
    )


if __name__ == "__main__":
    main()
