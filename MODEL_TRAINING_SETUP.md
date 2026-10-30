# Model Training Setup for DermaCare AI

I've set up a complete ML training pipeline for the skin analysis model. Here's what has been built and how to use it.

## What's Been Created

### 1. Enhanced Training Infrastructure

**Location**: `_ml-service/training/train.py`

Features:
- ✅ Validation split for model evaluation
- ✅ Early stopping to prevent overfitting
- ✅ Learning rate scheduling
- ✅ Data augmentation (random flips, rotations, color jitter)
- ✅ Comprehensive metrics (accuracy, F1, precision, recall)
- ✅ Best model checkpointing
- ✅ GPU support (CUDA)

### 2. Dataset Preparation Scripts

**Three options available:**

#### Option A: Kaggle Dataset (Recommended)
- Script: `_ml-service/datasets/prepare_dataset.py`
- Dataset: https://www.kaggle.com/datasets/bishalsharma000/facial-skin-datasets
- ~400+ images categorized by skin type
- Best for production-quality training

#### Option B: Sample Dataset (Quick Testing)
- Script: `_ml-service/datasets/create_sample_dataset.py`
- Use your own face images
- Generates random but plausible labels
- Good for testing the pipeline

#### Option C: Download Sample
- Script: `_ml-service/datasets/download_sample.py`
- Downloads public sample face images
- Quick way to get started

### 3. Model Architecture

**Location**: `_ml-service/models/network.py`

- ResNet-18 backbone (pretrained on ImageNet)
- Two output heads:
  - Observation head: 8 binary classifications (acne, redness, dark spots, etc.)
  - Skin type head: 4-class classification (normal, dry, oily, combination)

### 4. Documentation

- `ML_TRAINING_GUIDE.md` - Complete training guide
- `datasets/README.md` - Dataset preparation instructions

## How to Train the Model

### Step 1: Get Training Data

Choose one of these options:

**Option 1: Kaggle Dataset (Best)**
```bash
# Download from: https://www.kaggle.com/datasets/bishalsharma000/facial-skin-datasets
# Extract to a local directory

cd _ml-service
python datasets/prepare_dataset.py \
    --source /path/to/extracted/dataset/01_datasets_refined _dara \
    --output datasets/prepared
```

**Option 2: Your Own Images**
```bash
cd _ml-service
python datasets/create_sample_dataset.py \
    --images-dir /path/to/your/face/images \
    --output datasets/sample
```

**Option 3: Download Sample Images**
```bash
cd _ml-service
python datasets/download_sample.py --output datasets/raw/sample
python datasets/create_sample_dataset.py \
    --images-dir datasets/raw/sample/images \
    --output datasets/sample
```

### Step 2: Train the Model

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

**Parameters:**
- `--train-csv`: Training data CSV (required)
- `--val-csv`: Validation data CSV (optional)
- `--output`: Model output path (default: models/skin_model.pt)
- `--epochs`: Training epochs (default: 20)
- `--batch-size`: Batch size (default: 16)
- `--learning-rate`: Learning rate (default: 2e-4)
- `--patience`: Early stopping patience (default: 5)

### Step 3: Test the Model

```bash
cd _ml-service
python -c "
from inference.predict import Predictor
predictor = Predictor('models/skin_model.pt')
print('Model loaded:', predictor.model is not None)
"
```

### Step 4: Use the Trained Model

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

3. Restart the backend (it will now use the trained model)

## Training Output

The training script will show:
- Loss per epoch (train and validation)
- Observation accuracy (how well it detects skin issues)
- Skin type accuracy (how well it classifies skin type)
- F1 score, precision, recall
- Learning rate adjustments
- Best model checkpoint saving

Example output:
```
Epoch 1/20 (45.2s)
  LR: 0.000200
  Train Loss: 0.6234 | Val Loss: 0.5891
  Train - Obs Acc: 0.723, Type Acc: 0.685
  Val   - Obs Acc: 0.751, Type Acc: 0.712
  Val   - Type F1: 0.698, Precision: 0.705, Recall: 0.691
  ✓ Saved best model (val_loss: 0.5891)
```

## Expected Performance

With the Kaggle dataset (~400 images):
- **Skin type accuracy**: 70-80%
- **Observation accuracy**: 65-75%
- **Training time**: 30-60 minutes on CPU, 5-15 minutes on GPU

With custom datasets, performance will vary based on:
- Number of images (more is better)
- Label quality
- Image diversity
- Training epochs

## Improving the Model

To get better results:

1. **More Data**: 1000+ images recommended for production
2. **Better Labels**: Use dermatologist-validated observation scores
3. **Longer Training**: Increase epochs to 50-100
4. **Better Architecture**: Try EfficientNet or Vision Transformers
5. **Transfer Learning**: Fine-tune on larger skin datasets first

## Troubleshooting

**Out of Memory:**
- Reduce `--batch-size` to 8 or 4
- Use CPU: `CUDA_VISIBLE_DEVICES="" python training/train.py ...`

**Slow Training:**
- Use GPU if available
- Reduce image resolution in training script
- Increase batch size if memory allows

**Poor Performance:**
- Increase training epochs
- Adjust learning rate (try 1e-4 or 5e-5)
- Check dataset quality
- Add more data augmentation

## Next Steps

1. **Download dataset** (Kaggle or use your own)
2. **Prepare dataset** using the appropriate script
3. **Train the model** with the training script
4. **Test the model** with sample images
5. **Integrate** with the backend by updating configuration

The model is now ready to be trained with your chosen dataset!
