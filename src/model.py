"""
Predictive Model Module
=======================
Builds, trains, and evaluates a Random Forest classifier for predicting
30-day patient readmission. Uses stratified train-test splitting to handle
class imbalance common in readmission prediction tasks.
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple:
    """
    Trains a Random Forest classifier with stratified splitting and class
    weight balancing to address the class imbalance inherent in readmission data.

    Args:
        X: Feature matrix.
        y: Binary target (1 = readmitted within 30 days, 0 = not).
        test_size: Fraction of data reserved for testing.
        random_state: Seed for reproducibility.

    Returns:
        Tuple of (trained model, X_test, y_test, y_pred, y_proba).
    """
    logger.info("Training Random Forest classifier...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")

    # Log results
    logger.info(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")
    logger.info(f"5-Fold CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    logger.info(f"Test Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    logger.info(f"Test Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
    logger.info(f"Test Recall:    {recall_score(y_test, y_pred, zero_division=0):.4f}")
    logger.info(f"Test F1 Score:  {f1_score(y_test, y_pred, zero_division=0):.4f}")
    logger.info(f"Test ROC-AUC:   {roc_auc_score(y_test, y_proba):.4f}")
    logger.info(f"\n{classification_report(y_test, y_pred, zero_division=0)}")

    # Generate evaluation plots
    _plot_confusion_matrix(y_test, y_pred)
    _plot_roc_curve(y_test, y_proba)
    _plot_feature_importance(model, X.columns)

    return model, X_test, y_test, y_pred, y_proba


def _plot_confusion_matrix(y_true, y_pred) -> None:
    """Saves a confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["Not Readmitted", "Readmitted"],
        yticklabels=["Not Readmitted", "Readmitted"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix: 30-Day Readmission Prediction")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)
    logger.info("Saved: outputs/confusion_matrix.png")


def _plot_roc_curve(y_true, y_proba) -> None:
    """Saves an ROC curve plot."""
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="steelblue", lw=2, label=f"ROC Curve (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], color="grey", linestyle="--", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve: 30-Day Readmission Prediction")
    ax.legend(loc="lower right")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "roc_curve.png", dpi=150)
    plt.close(fig)
    logger.info("Saved: outputs/roc_curve.png")


def _plot_feature_importance(model, feature_names) -> None:
    """Saves a horizontal bar chart of Random Forest feature importances."""
    importances = pd.Series(model.feature_importances_, index=feature_names)
    importances = importances.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    importances.plot(kind="barh", color="steelblue", ax=ax)
    ax.set_xlabel("Mean Decrease in Impurity")
    ax.set_title("Random Forest Feature Importances")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)
    logger.info("Saved: outputs/feature_importance.png")
