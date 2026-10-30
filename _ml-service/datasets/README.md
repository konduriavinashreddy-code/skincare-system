# Dataset Preparation for DermaCare AI Training

This directory contains scripts to prepare datasets for training the skin analysis model.

## Options for Getting Training Data

### Option 1: Kaggle Dataset (Recommended)

Use the "Facial skin datasets" from Kaggle which contains ~400+ images categorized by skin type.

**Steps:**

1. **Download the dataset**
   - Visit: https://www.kaggle.com/datasets/bishalsharma000/facial-skin-datasets
   - Download and extract to a local directory
   - Extracted structure should look like:
     ```
     facial-skin-datasets/
     ├── 01_datasets_refined _dara/
     │   ├── acne-prone-skin/
     │   ├── dry-skin/
     │   ├── oily-skin/
     │   └── healthy/
     ```

2. **Prepare the dataset**
   ```bash
   cd _ml-service
   python datasets/prepare_dataset.py \
       --source /path/to/facial-skin-datasets/01_datasets_refined _dara \
       --output datasets/prepared
   ```

   This will:
   - Copy all images to a single directory
   - Create train/val/test CSV files with labels
   - Assign heuristic observation scores based on skin type
   - Split data: 80% train, 10% val, 10% test

### Option 2: Sample Dataset (For Testing)

If you have a folder of face images and want to test the training pipeline:

```bash
cd _ml-service
python datasets/create_sample_dataset.py \
    --images-dir /path/to/your/images \
    --output datasets/sample
```

This creates CSV files with random but plausible labels for your images.

### Option 3: Custom Dataset

Create your own CSV file with the following format:

```csv
image,acne_like_features,redness,dark_spots,oiliness,dryness,uneven_tone,texture,fine_lines,skin_type
image1.jpg,0.85,0.62,0.41,0.72,0.28,0.61,0.51,0.19,oily
image2.jpg,0.18,0.39,0.31,0.12,0.88,0.49,0.68,0.52,dry
```

- `image`: Path to image file (relative to CSV directory)
- Observation scores: Float values between 0-1
- `skin_type`: One of "normal", "dry", "oily", "combination"

## Training the Model

Once you have prepared the dataset:

```bash
cd _ml-service
python training/train.py \
    --train-csv datasets/prepared/train_labels.csv \
    --val-csv datasets/prepared/val_labels.csv \
    --output models/skin_model.pt \
    --epochs 20 \
    --batch-size 16
```

## Dataset Requirements

- **Image Format**: JPG, JPEG, PNG, or WEBP
- **Image Size**: Any size (will be resized to 224x224 during training)
- **Minimum Images**: At least 100 images recommended for basic training
- **Recommended**: 500+ images for better performance

## Label Guidelines

For production use, observation scores should be based on:
- **acne_like_features**: Presence of acne, pimples, bumps (0-1)
- **redness**: Skin redness, inflammation (0-1)
- **dark_spots**: Hyperpigmentation, dark marks (0-1)
- **oiliness**: Skin oiliness, shine (0-1)
- **dryness**: Skin dryness, flakiness (0-1)
- **uneven_tone**: Skin tone irregularities (0-1)
- **texture**: Skin texture irregularities (0-1)
- **fine_lines**: Presence of fine lines, wrinkles (0-1)

## Notes

- The Kaggle dataset uses heuristic scores based on skin type categories
- For better model performance, use manually labeled observation data
- The current approach is suitable for demonstration and prototyping
- Production models would require dermatologist-validated labels
