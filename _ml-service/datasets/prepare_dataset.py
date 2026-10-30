"""
Dataset preparation script for DermaCare AI skin analysis model.
This script prepares the Kaggle "Facial skin datasets" for training.
"""

import os
import csv
import shutil
from pathlib import Path
from typing import Dict, List
import random

# Skin type to observation score mappings
# These are heuristic mappings based on typical skin characteristics
SKIN_TYPE_OBSERVATIONS = {
    "acne-prone-skin": {
        "acne_like_features": 0.9,
        "redness": 0.6,
        "dark_spots": 0.4,
        "oiliness": 0.7,
        "dryness": 0.3,
        "uneven_tone": 0.6,
        "texture": 0.5,
        "fine_lines": 0.2
    },
    "dry-skin": {
        "acne_like_features": 0.2,
        "redness": 0.4,
        "dark_spots": 0.3,
        "oiliness": 0.1,
        "dryness": 0.9,
        "uneven_tone": 0.5,
        "texture": 0.7,
        "fine_lines": 0.5
    },
    "oily-skin": {
        "acne_like_features": 0.5,
        "redness": 0.3,
        "dark_spots": 0.3,
        "oiliness": 0.9,
        "dryness": 0.1,
        "uneven_tone": 0.4,
        "texture": 0.4,
        "fine_lines": 0.2
    },
    "healthy": {
        "acne_like_features": 0.1,
        "redness": 0.2,
        "dark_spots": 0.2,
        "oiliness": 0.4,
        "dryness": 0.3,
        "uneven_tone": 0.2,
        "texture": 0.2,
        "fine_lines": 0.2
    }
}

# Map Kaggle dataset categories to our model's skin types
SKIN_TYPE_MAPPING = {
    "acne-prone-skin": "oily",  # Acne-prone typically oily
    "dry-skin": "dry",
    "oily-skin": "oily",
    "healthy": "normal"
}

OBSERVATIONS = ["acne_like_features", "redness", "dark_spots", "oiliness", "dryness", "uneven_tone", "texture", "fine_lines"]


def add_random_variation(scores: Dict[str, float], variation: float = 0.15) -> Dict[str, float]:
    """Add small random variation to observation scores to prevent overfitting."""
    return {k: max(0.0, min(1.0, v + random.uniform(-variation, variation))) for k, v in scores.items()}


def prepare_dataset(
    source_dir: Path,
    output_dir: Path,
    train_split: float = 0.8,
    val_split: float = 0.1
):
    """
    Prepare dataset from Kaggle facial skin datasets structure.

    Args:
        source_dir: Path to downloaded Kaggle dataset
        output_dir: Path where prepared dataset will be saved
        train_split: Fraction of data for training
        val_split: Fraction of data for validation
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output directories
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Find all skin type directories in source
    skin_type_dirs = {}
    for category in SKIN_TYPE_MAPPING.keys():
        category_path = source_dir / category
        if category_path.exists() and category_path.is_dir():
            skin_type_dirs[category] = list(category_path.glob("*.*"))
            print(f"Found {len(skin_type_dirs[category])} images in {category}")
    
    if not skin_type_dirs:
        print("ERROR: No skin type directories found in source directory.")
        print(f"Expected directories: {list(SKIN_TYPE_MAPPING.keys())}")
        print(f"Source directory: {source_dir}")
        return
    
    # Collect all images with their labels
    all_data = []
    for category, images in skin_type_dirs.items():
        for img_path in images:
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                all_data.append({
                    'source_path': img_path,
                    'category': category,
                    'skin_type': SKIN_TYPE_MAPPING[category]
                })
    
    print(f"Total images found: {len(all_data)}")
    
    # Shuffle and split
    random.shuffle(all_data)
    n_total = len(all_data)
    n_train = int(n_total * train_split)
    n_val = int(n_total * val_split)
    
    train_data = all_data[:n_train]
    val_data = all_data[n_train:n_train + n_val]
    test_data = all_data[n_train + n_val:]
    
    print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
    
    # Process each split
    for split_name, split_data in [('train', train_data), ('val', val_data), ('test', test_data)]:
        csv_path = output_dir / f"{split_name}_labels.csv"
        
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            header = ['image'] + OBSERVATIONS + ['skin_type']
            writer.writerow(header)
            
            for idx, item in enumerate(split_data):
                # Copy image
                img_extension = item['source_path'].suffix
                new_filename = f"{split_name}_{idx}{img_extension}"
                dest_path = images_dir / new_filename
                shutil.copy2(item['source_path'], dest_path)
                
                # Get observation scores with variation
                base_scores = SKIN_TYPE_OBSERVATIONS[item['category']]
                scores = add_random_variation(base_scores)
                
                # Write row
                row = [new_filename] + [scores[obs] for obs in OBSERVATIONS] + [item['skin_type']]
                writer.writerow(row)
        
        print(f"Created {csv_path} with {len(split_data)} samples")
    
    print(f"\nDataset preparation complete!")
    print(f"Images saved to: {images_dir}")
    print(f"CSV files saved to: {output_dir}")
    print(f"\nTo train the model, run:")
    print(f"  python training/train.py --csv {output_dir / 'train_labels.csv'} --output models/skin_model.pt --epochs 20")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare Kaggle facial skin dataset for training")
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to downloaded Kaggle dataset (e.g., path/to/01_datasets_refined _dara)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/prepared"),
        help="Output directory for prepared dataset"
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
    
    prepare_dataset(
        source_dir=args.source,
        output_dir=args.output,
        train_split=args.train_split,
        val_split=args.val_split
    )


if __name__ == "__main__":
    main()
