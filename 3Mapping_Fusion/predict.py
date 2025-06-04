#!/usr/bin/python
# -*- coding: gbk -*-

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, MinMaxScaler
import os
import matplotlib.pyplot as plt
import seaborn as sns
from lightning_fabric.utilities.seed import seed_everything
from sklearn.utils import resample

class Config:
    def __init__(self):
        # Data loading parameters
        self.batch_size = 32

        # Feature segmentation configuration
        self.feature_names = [  # Feature names for each segment
            ["BM25", "BM25 Score"],   # Segment 1
            ["LLM-S", "LLM-S Score"], # Segment 2
            ["LLM-A"]                 # Segment 3
        ]

        # Model parameters
        self.hidden_dim = 256           # Hidden dimension for each expert
        self.num_heads = 4              # Number of attention heads
        self.num_experts = 5            # Number of experts (same as number of feature segments)
        self.top_k = 3                  # Number of experts to use
        self.dropout = 0.5              # Dropout probability

        # Training parameters
        self.epochs = 50                # Maximum number of training epochs
        self.learning_rate = 1e-4       # Initial learning rate
        self.weight_decay = 1e-4        # Regularization weight
        self.lr_gamma = 0.95            # Learning rate decay factor
        self.patience = 5               # Early stopping patience

        # File paths
        self.input_path = "MoE_input.csv"
        self.output_path = "predictions.csv"
        # self.metrics_path = "best_model_metrics.csv"

class FusionSplitDataset(Dataset):
    def __init__(self, dataframe, config):
        df = dataframe.copy()
        self.label_encoder = LabelEncoder()
        self.gt = torch.tensor(self.label_encoder.fit_transform(df['ground truth']), dtype=torch.long)

        # Process features based on segmentation configuration
        self.feature_segments = []
        for segment in config.feature_names:
            features = []
            for feature_name in segment:
                if feature_name.endswith("Score"):
                    # Normalize numerical features
                    scaled_feature = MinMaxScaler().fit_transform(df[[feature_name]])
                    features.append(scaled_feature)
                else:
                    # Apply one-hot encoding for categorical features
                    one_hot_enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
                    one_hot_feature = one_hot_enc.fit_transform(df[[feature_name]])
                    features.append(one_hot_feature)
            # Concatenate features for the segment
            segment_features = np.hstack(features)
            self.feature_segments.append(torch.tensor(segment_features, dtype=torch.float32))

        self.project = df['Project'].tolist()
        self.indices = df.index.to_numpy()  # Store indices for use in prediction output

    def __len__(self):
        return len(self.gt)

    def __getitem__(self, idx):
        segments = [segment[idx] for segment in self.feature_segments]
        return segments, self.gt[idx], self.indices[idx]

class ExpertModule(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim=2, num_heads=4):
        super(ExpertModule, self).__init__()
        # Dimension expansion
        self.linear1 = nn.Linear(input_dim, 4 * hidden_dim)
        self.norm1 = nn.LayerNorm(4 * hidden_dim)

        # Dimension reduction
        self.linear2 = nn.Linear(4 * hidden_dim, 2 * hidden_dim)
        self.norm2 = nn.LayerNorm(2 * hidden_dim)

        self.linear3 = nn.Linear(2 * hidden_dim, hidden_dim)
        self.norm3 = nn.LayerNorm(hidden_dim)

        self.linear4 = nn.Linear(hidden_dim, output_dim)

        # Multi-head attention
        self.attn = nn.MultiheadAttention(embed_dim=4 * hidden_dim, num_heads=num_heads, batch_first=True)

        # Activation and dropout
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        # Expand dimensions
        x = self.linear1(x)
        x = self.activation(x)
        x = self.norm1(x)
        x = x.unsqueeze(1)  # Add time dimension for attention

        # Apply multi-head attention with residual connection
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + self.dropout(attn_out))

        # Reduce dimensions
        x = self.linear2(x)
        x = self.activation(x)
        x = self.norm2(x)

        x = self.linear3(x)
        x = self.activation(x)
        x = self.norm3(x)

        # Final output layer
        x = self.linear4(x.squeeze(1))  # Remove time dimension
        return x

class GatingNetwork(nn.Module):
    def __init__(self, input_dim, num_experts, hidden_dim=64, top_k=2):
        super(GatingNetwork, self).__init__()
        self.top_k = top_k
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, num_experts)
        )

    def forward(self, x):
        logits = self.fc(x)
        topk_mask = torch.topk(logits, self.top_k, dim=1).indices
        gated = torch.full_like(logits, -float('inf'))
        gated.scatter_(1, topk_mask, logits.gather(1, topk_mask))
        return F.softmax(gated, dim=1)

class MoEStructurallyBoundClassifier(nn.Module):
    def __init__(self, input_dims, hidden_dim, num_classes, top_k=2, dropout=0.3, num_heads=4):
        super(MoEStructurallyBoundClassifier, self).__init__()
        self.num_experts = len(input_dims)
        self.experts = nn.ModuleList([
            ExpertModule(input_dim, hidden_dim, num_classes, num_heads=num_heads)
            for input_dim in input_dims
        ])
        self.gating = GatingNetwork(sum(input_dims), self.num_experts, top_k=top_k)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x_parts):
        expert_outputs = torch.stack(
            [expert(x_parts[i]) for i, expert in enumerate(self.experts)],
            dim=1
        )
        gating_input = torch.cat(x_parts, dim=1)
        gate_weights = self.gating(gating_input).unsqueeze(-1)
        output = (expert_outputs * gate_weights).sum(dim=1)
        return output, gate_weights.squeeze(-1)

def train(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    for x_parts, y, _ in dataloader:
        x_parts = [x.to(device) for x in x_parts]
        y = y.to(device)
        optimizer.zero_grad()
        out, _ = model(x_parts)
        loss = criterion(out, y)
        loss.backward()

        # Gradient normalization
        for param in model.parameters():
            if param.grad is not None:
                param.grad.data /= len(dataloader)

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1)

        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)

def evaluate(model, dataloader, criterion, device, label_encoder=None):
    model.eval()
    total_loss = 0
    all_preds, all_labels = [], []

    with torch.no_grad():
        for x_parts, y, _ in dataloader:
            x_parts = [x.to(device) for x in x_parts]
            y = y.to(device)
            out, _ = model(x_parts)
            loss = criterion(out, y)
            total_loss += loss.item()
            pred = out.argmax(dim=1)
            all_preds.extend(pred.cpu().numpy())
            all_labels.extend(y.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    if label_encoder:
        none_index = label_encoder.transform(["non"])[0] if "non" in label_encoder.classes_ else 0
    else:
        none_index = 0
    y_true, y_pred = np.array(all_labels), np.array(all_preds)
    tp = np.sum((y_pred == none_index) & (y_true == none_index))
    pred_none_total = np.sum(y_pred == none_index)
    real_none_total = np.sum(y_true == none_index)
    precision = tp / pred_none_total if pred_none_total > 0 else 0.0
    recall = tp / real_none_total if real_none_total > 0 else 0.0

    return avg_loss, precision, recall

def balance_data(df, method="oversample"):
    """
    Balance data using oversampling or undersampling.
    """
    label_counts = df['GT'].value_counts()
    print(f"Original class distribution:\n{label_counts}")

    df_majority = df[df['GT'] != 'non']
    df_minority = df[df['GT'] == 'non']

    if method == "oversample":
        df_minority_upsampled = resample(
            df_minority,
            replace=True,
            n_samples=len(df_majority)
        )
        df_balanced = pd.concat([df_majority, df_minority_upsampled])

    elif method == "downsample":
        df_majority_downsampled = resample(
            df_majority,
            replace=False,
            n_samples=len(df_minority)
        )
        df_balanced = pd.concat([df_majority_downsampled, df_minority])

    else:
        raise ValueError("Method must be 'oversample' or 'downsample'.")

    balanced_counts = df_balanced['GT'].value_counts()
    print(f"Balanced class distribution:\n{balanced_counts}")

    return df_balanced

def cross_project_train_and_predict(df, device, config):
    df = df.copy()
    balance_df = balance_data(df, method="oversample")
    df["Predicted"] = ""  # Add column for prediction output
    project_list = df['Project'].unique().tolist()

    project_metrics = {}

    for held_out in project_list:
        print(f"\nTraining with [{held_out}] as validation set")
        train_df = balance_df[balance_df['Project'] != held_out]
        val_df = balance_df[balance_df['Project'] == held_out]

        train_set = FusionSplitDataset(train_df, config)
        val_set = FusionSplitDataset(val_df, config)
        test_df = df[df['Project'] == held_out]
        test_set = FusionSplitDataset(test_df, config)

        class_counts = train_df['GT'].value_counts()
        class_weights = torch.tensor(1.0 / class_counts.iloc[:].values, dtype=torch.float32).to(device)

        sample_weights = train_df['GT'].apply(
            lambda x: class_weights[train_set.label_encoder.transform([x])[0]].item()
        )
        sample_weights = sample_weights.to_numpy(dtype=np.float32)

        sampler = WeightedRandomSampler(
            weights=torch.tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True)

        train_loader = DataLoader(train_set, batch_size=config.batch_size, sampler=sampler)
        val_loader = DataLoader(val_set, batch_size=config.batch_size, shuffle=False)
        test_loader = DataLoader(test_set, batch_size=config.batch_size, shuffle=False)

        input_dims = [segment.shape[1] for segment in train_set.feature_segments]
        num_classes = len(train_set.label_encoder.classes_)

        model = MoEStructurallyBoundClassifier(
            input_dims=input_dims,
            hidden_dim=config.hidden_dim,
            num_classes=num_classes,
            top_k=config.top_k,
            dropout=config.dropout,
            num_heads=config.num_heads
        ).to(device)

        criterion = nn.CrossEntropyLoss(weight=class_weights)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=config.lr_gamma)

        best_loss = float('inf')
        best_precision = 0
        best_recall = 0
        counter = 0

        for epoch in range(config.epochs):
            train_loss = train(model, train_loader, criterion, optimizer, device)
            val_loss, precision, recall = evaluate(model, val_loader, criterion, device, val_set.label_encoder)
            print(f"[{held_out}] Epoch {epoch+1} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | P: {precision:.3f} | R: {recall:.3f}")
            scheduler.step()

            if val_loss < best_loss:
                best_loss = val_loss
                best_precision = precision
                best_recall = recall
                torch.save(model.state_dict(), f"{held_out}_best.pth")
                counter = 0
            else:
                counter += 1
                if counter >= config.patience:
                    break

        model.load_state_dict(torch.load(f"{held_out}_best.pth"))
        model.eval()

        test_loss, test_precision, test_recall = evaluate(model, test_loader, criterion, device, test_set.label_encoder)
        test_f1 = 2 * test_precision * test_recall / (test_precision + test_recall) if (test_precision + test_recall) > 0 else 0.0
        print(f"[{held_out}] Test Set | Loss: {test_loss:.4f} | Precision: {test_precision:.3f} | Recall: {test_recall:.3f} | F1: {test_f1:.3f}")

        project_metrics[held_out] = {
            "F1": test_f1,
            "Precision": test_precision,
            "Recall": test_recall
        }

        preds, idxs = [], []
        with torch.no_grad():
            for x_parts, _, idx in test_loader:
                x_parts = [x.to(device) for x in x_parts]
                out, _ = model(x_parts)
                pred = out.argmax(dim=1).cpu().numpy()
                preds.extend(pred)
                idxs.extend(idx.numpy())
        decoded = test_set.label_encoder.inverse_transform(preds)
        df.loc[idxs, "Predicted"] = decoded

    f1_scores = [metrics["F1"] for metrics in project_metrics.values()]
    avg_f1 = sum(f1_scores) / len(f1_scores) if len(f1_scores) > 0 else 0.0
    print(f"\nAverage F1 Score across all projects: {avg_f1:.3f}")

    metrics_df = pd.DataFrame.from_dict(project_metrics, orient="index")
    # metrics_df.to_csv(config.metrics_path, index_label="Project")
    # print(f"Best model metrics saved to: {config.metrics_path}")

    return df

if __name__ == "__main__":
    seed_everything(3407)

    config = Config()
    df = pd.read_csv(config.input_path)
    device = torch.device("cuda:4" if torch.cuda.is_available() else "cpu")

    updated_df = cross_project_train_and_predict(df, device, config)
    updated_df.to_csv(config.output_path, index=False)
    print(f"Prediction results saved to: {config.output_path}")
