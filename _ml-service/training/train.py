"""
Enhanced training script for DermaCare AI skin analysis model.
Includes validation, early stopping, learning rate scheduling, and comprehensive metrics.
"""

import argparse
import csv
from pathlib import Path
import time
from typing import Dict, Tuple

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

from models.network import OBSERVATIONS, SKIN_TYPES, SkinObservationNet


class LabeledImages(Dataset):
    """Dataset for skin analysis with observation labels and skin type."""
    
    def __init__(self, csv_path: Path, transform=None):
        self.root = csv_path.parent
        with csv_path.open(newline="", encoding="utf-8") as source:
            self.rows = list(csv.DictReader(source))
        
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(10),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transform
    
    def __len__(self):
        return len(self.rows)
    
    def __getitem__(self, index):
        row = self.rows[index]
        image = Image.open(self.root / row["image"]).convert("RGB")
        labels = torch.tensor([float(row[key]) for key in OBSERVATIONS], dtype=torch.float32)
        skin_type_idx = SKIN_TYPES.index(row["skin_type"])
        return self.transform(image), labels, skin_type_idx


class EarlyStopping:
    """Early stopping to prevent overfitting."""
    
    def __init__(self, patience: int = 5, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
    
    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False
        
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        return False


def compute_metrics(
    predictions: torch.Tensor,
    targets: torch.Tensor,
    type_predictions: torch.Tensor,
    type_targets: torch.Tensor
) -> Dict[str, float]:
    """Compute comprehensive metrics for model evaluation."""
    
    # Binary classification metrics for observations
    pred_binary = (predictions.sigmoid() > 0.5).float()
    target_binary = (targets > 0.5).float()
    
    # Calculate accuracy for each observation
    obs_accuracies = []
    for i in range(len(OBSERVATIONS)):
        acc = (pred_binary[:, i] == target_binary[:, i]).float().mean().item()
        obs_accuracies.append(acc)
    
    avg_obs_accuracy = sum(obs_accuracies) / len(obs_accuracies)
    
    # Skin type classification metrics
    type_pred_labels = type_predictions.argmax(dim=1).cpu().numpy()
    type_target_labels = type_targets.cpu().numpy()
    
    type_accuracy = accuracy_score(type_target_labels, type_pred_labels)
    type_f1 = f1_score(type_target_labels, type_pred_labels, average='weighted', zero_division=0)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        type_target_labels, type_pred_labels, average='weighted', zero_division=0
    )
    
    return {
        'avg_obs_accuracy': avg_obs_accuracy,
        'type_accuracy': type_accuracy,
        'type_f1': type_f1,
        'type_precision': precision,
        'type_recall': recall
    }


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    binary_loss_fn: nn.Module,
    type_loss_fn: nn.Module,
    device: torch.device
) -> Tuple[float, Dict[str, float]]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    all_obs_preds = []
    all_obs_targets = []
    all_type_preds = []
    all_type_targets = []
    
    for images, observations, skin_types in loader:
        images = images.to(device)
        observations = observations.to(device)
        skin_types = skin_types.to(device)
        
        optimizer.zero_grad()
        prediction, type_prediction = model(images)
        
        loss = binary_loss_fn(prediction, observations) + type_loss_fn(type_prediction, skin_types)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        # Collect predictions for metrics
        all_obs_preds.append(prediction.detach())
        all_obs_targets.append(observations.detach())
        all_type_preds.append(type_prediction.detach())
        all_type_targets.append(skin_types.detach())
    
    # Compute metrics
    all_obs_preds = torch.cat(all_obs_preds, dim=0)
    all_obs_targets = torch.cat(all_obs_targets, dim=0)
    all_type_preds = torch.cat(all_type_preds, dim=0)
    all_type_targets = torch.cat(all_type_targets, dim=0)
    
    metrics = compute_metrics(all_obs_preds, all_obs_targets, all_type_preds, all_type_targets)
    
    return total_loss / len(loader), metrics


def validate(
    model: nn.Module,
    loader: DataLoader,
    binary_loss_fn: nn.Module,
    type_loss_fn: nn.Module,
    device: torch.device
) -> Tuple[float, Dict[str, float]]:
    """Validate the model."""
    model.eval()
    total_loss = 0.0
    all_obs_preds = []
    all_obs_targets = []
    all_type_preds = []
    all_type_targets = []
    
    with torch.no_grad():
        for images, observations, skin_types in loader:
            images = images.to(device)
            observations = observations.to(device)
            skin_types = skin_types.to(device)
            
            prediction, type_prediction = model(images)
            
            loss = binary_loss_fn(prediction, observations) + type_loss_fn(type_prediction, skin_types)
            total_loss += loss.item()
            
            all_obs_preds.append(prediction)
            all_obs_targets.append(observations)
            all_type_preds.append(type_prediction)
            all_type_targets.append(skin_types)
    
    # Compute metrics
    all_obs_preds = torch.cat(all_obs_preds, dim=0)
    all_obs_targets = torch.cat(all_obs_targets, dim=0)
    all_type_preds = torch.cat(all_type_preds, dim=0)
    all_type_targets = torch.cat(all_type_targets, dim=0)
    
    metrics = compute_metrics(all_obs_preds, all_obs_targets, all_type_preds, all_type_targets)
    
    return total_loss / len(loader), metrics


def train(
    train_csv: Path,
    val_csv: Path,
    output: Path,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    patience: int
):
    """Train the skin analysis model with validation and early stopping."""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create datasets
    print("Loading training data...")
    train_dataset = LabeledImages(train_csv)
    print(f"Training samples: {len(train_dataset)}")
    
    if val_csv and val_csv.exists():
        print("Loading validation data...")
        val_dataset = LabeledImages(val_csv, transform=transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]))
        print(f"Validation samples: {len(val_dataset)}")
    else:
        # Split training data if no validation set
        val_split = 0.1
        val_size = int(len(train_dataset) * val_split)
        train_size = len(train_dataset) - val_size
        train_dataset, val_dataset = random_split(train_dataset, [train_size, val_size])
        print(f"Split training data: {train_size} train, {val_size} validation")
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Initialize model
    print("Initializing model...")
    model = SkinObservationNet(pretrained=True).to(device)
    
    # Optimizer and loss functions
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    binary_loss = nn.BCEWithLogitsLoss()
    type_loss = nn.CrossEntropyLoss()
    
    # Early stopping
    early_stopping = EarlyStopping(patience=patience)
    
    # Training loop
    best_val_loss = float('inf')
    print(f"\nStarting training for {epochs} epochs...")
    print("-" * 80)
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Train
        train_loss, train_metrics = train_epoch(
            model, train_loader, optimizer, binary_loss, type_loss, device
        )
        
        # Validate
        val_loss, val_metrics = validate(
            model, val_loader, binary_loss, type_loss, device
        )
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        # Print metrics
        epoch_time = time.time() - epoch_start
        print(f"\nEpoch {epoch + 1}/{epochs} ({epoch_time:.1f}s)")
        print(f"  LR: {current_lr:.6f}")
        print(f"  Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"  Train - Obs Acc: {train_metrics['avg_obs_accuracy']:.3f}, Type Acc: {train_metrics['type_accuracy']:.3f}")
        print(f"  Val   - Obs Acc: {val_metrics['avg_obs_accuracy']:.3f}, Type Acc: {val_metrics['type_accuracy']:.3f}")
        print(f"  Val   - Type F1: {val_metrics['type_f1']:.3f}, Precision: {val_metrics['type_precision']:.3f}, Recall: {val_metrics['type_recall']:.3f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            output.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "state_dict": model.state_dict(),
                "observations": OBSERVATIONS,
                "skin_types": SKIN_TYPES,
                "val_loss": val_loss,
                "val_metrics": val_metrics
            }, output)
            print(f"  ✓ Saved best model (val_loss: {val_loss:.4f})")
        
        # Early stopping
        if early_stopping(val_loss):
            print(f"\nEarly stopping triggered after {epoch + 1} epochs")
            break
    
    print("-" * 80)
    print(f"\nTraining complete!")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Model saved to: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Train DermaCare ResNet-18 model with validation and early stopping"
    )
    parser.add_argument("--train-csv", type=Path, required=True, help="Training data CSV")
    parser.add_argument("--val-csv", type=Path, default=None, help="Validation data CSV (optional)")
    parser.add_argument("--output", type=Path, default=Path("models/skin_model.pt"), help="Output model path")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    
    args = parser.parse_args()
    
    train(
        train_csv=args.train_csv,
        val_csv=args.val_csv,
        output=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        patience=args.patience
    )


if __name__ == "__main__":
    main()
