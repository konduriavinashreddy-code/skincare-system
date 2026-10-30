# ML Training Guide for DermaCare AI

This guide explains how to train a skin analysis model using Kaggle datasets.

## Prerequisites

- Python 3.11+
- PyTorch and dependencies installed (run `pip install -r requirements.txt`)
- Kaggle account and API key (optional, for downloading datasets)

## Step 1: Download Dataset

We'll use the "Facial skin datasets" from Kaggle which contains images categorized by skin type.

### Option A: Manual Download

1. Visit: https://www.kaggle.com/datasets/bishalsharma000/facial-skin-datasets
2. Download the dataset
3. Extract it to a known location (e.g., `datasets/raw/facial-skin-datasets`)

### Option B: Using Kaggle API

```bash
# Install kaggle API
pip install kaggle

# Download dataset
kaggle datasets download -d bishalsharma000/facial-skin-datasets -p datasets/raw

# Extract
cd datasets/raw
unzip facial-skin-datasets.zip
```

## Step 2: Prepare Dataset

Once you have the dataset downloaded, prepare it for training:

```bash
cd _ml-service
python datasets/prepare_dataset.py \
    --source ../datasets/raw/01_datasets_refined _dara \
    --output datasets/prepared
```

This will:
- Organize images into a single directory
- Create CSV files with labels for train/val/test splits
- Add heuristic observation scores based on skin type
- Apply random variation to prevent overfitting

The script will create:
- `datasets/prepared/images/` - All training images
- `datasets/prepared/train_labels.csv` - Training labels
- `datasets/prepared/val_labels.csv` - Validation labels
- `datasets/prepared/test_labels.csv` - Test labels

## Step 3: Train the Model

Train the model with the prepared dataset:

```bash
cd _ml-service
python training/train.py \
    --train-csv datasets/prepared/train_labels.csv \
    --val-csv datasets/prepared/val_labels.csv \
    --output models/skin_model.pt \
    --epochs 20 \
    --batch-size 16 \
    --learning-rate 2e-4 \
    --patience 5
```

### Training Parameters

- `--train-csv`: Path to training CSV file (required)
- `--val-csv`: Path to validation CSV file (optional, will split from train if not provided)
- `--output`: Output path for the trained model (default: models/skin_model.pt)
- `--epochs`: Number of training epochs (default: 20)
- `--batch-size`: Batch size for training (default: 16)
- `--learning-rate`: Learning rate (default: 2e-4)
- `--patience`: Early stopping patience (default: 5)

### Training Features

The enhanced training script includes:
- **Validation**: Evaluates model on validation set each epoch
- **Early Stopping**: Stops training if validation loss doesn't improve
- **Learning Rate Scheduling**: Reduces LR when validation loss plateaus
- **Data Augmentation**: Random flips, rotations, and color jitter
- **Comprehensive Metrics**: Accuracy, F1 score, precision, recall for both observations and skin type
- **Best Model Saving**: Automatically saves the model with best validation loss

## Step 4: Test the Model

After training, test the model:

```bash
cd _ml-service
python -c "
from inference.predict import Predictor
predictor = Predictor('models/skin_model.pt')
print('Model loaded successfully:', predictor.model is not None)
"
```

## Step 5: Update Backend Configuration

To use the trained model in the backend:

1. Update `_backend/.env`:
   ```
   AI_MODE=model
   ML_SERVICE_URL=http://localhost:8001
   ```

2. Start the ML service:
   ```bash
   cd _ml-service
   uvicorn main:app --reload --port 8001
   ```

3. Restart the backend (it will now use the ML service instead of mock mode)

## Dataset Structure

The training CSV should have the following format:

```csv
image,acne_like_features,redness,dark_spots,oiliness,dryness,uneven_tone,texture,fine_lines,skin_type
train_0.jpg,0.85,0.62,0.41,0.72,0.28,0.61,0.51,0.19,oily
train_1.jpg,0.18,0.39,0.31,0.12,0.88,0.49,0.68,0.52,dry
...
```

- `image`: Filename of the image (relative to CSV parent directory)
- `acne_like_features`, `redness`, etc.: Float values between 0-1 indicating severity
- `skin_type`: One of "normal", "dry", "oily", "combination"

## Model Architecture

The model uses a ResNet-18 backbone with two output heads:
1. **Observation Head**: Predicts 8 binary observations (acne, redness, dark spots, etc.)
2. **Skin Type Head**: Predicts 4-class skin type (normal, dry, oily, combination)

## Troubleshooting

### Out of Memory Error
If you get CUDA out of memory errors:
- Reduce `--batch-size` (try 8 or 4)
- Use CPU training by setting environment variable: `CUDA_VISIBLE_DEVICES=""`

### Slow Training
If training is slow:
- Use GPU if available (CUDA)
- Reduce image resolution in transforms
- Increase batch size if memory allows

### Poor Performance
If model performance is poor:
- Increase training epochs
- Adjust learning rate (try 1e-4 or 5e-5)
- Add more data augmentation
- Check dataset quality and labels

## Notes

- The current dataset uses heuristic observation scores based on skin type categories
- For production use, you would need manually labeled observation data
- The model is a baseline and can be improved with:
  - More diverse training data
  - Better labeling
  - More sophisticated architectures (EfficientNet, Vision Transformers)
  - Multi-task learning with auxiliary tasks
