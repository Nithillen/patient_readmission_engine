"""
SHAP Explainability Module
==========================
Generates SHAP (SHapley Additive exPlanations) visualizations to interpret
the Random Forest model's predictions. These visualizations are designed
for data storytelling to non-technical stakeholders (hospital administrators,
clinical leads) and technical audiences alike.

SHAP values decompose each prediction into the contribution of each feature,
enabling clinicians to understand exactly why a patient was flagged as
high-risk for readmission.
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


def generate_shap_analysis(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    max_display: int = 15,
) -> None:
    """
    Generates a full suite of SHAP visualizations for model interpretability.

    Plots generated:
        1. Global Summary Plot (beeswarm) - Which features matter most overall.
        2. Global Bar Plot - Mean absolute SHAP values per feature.
        3. Individual Force Plot - Why the model made a specific prediction.
        4. Dependence Plot - How a single feature interacts with the prediction.

    Args:
        model: Trained scikit-learn model.
        X_test: Test feature matrix.
        y_test: Test target series.
        max_display: Maximum number of features to display in summary plots.
    """
    logger.info("Generating SHAP explainability analysis...")

    # Create SHAP TreeExplainer (optimized for tree-based models)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    # For binary classification, shap_values is a list [class_0, class_1]
    # We use class_1 (readmitted) for interpretation
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]
    else:
        shap_vals = shap_values

    # 1. Global Summary Plot (Beeswarm)
    logger.info("Generating SHAP Summary Plot (Beeswarm)...")
    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        shap_vals,
        X_test,
        max_display=max_display,
        show=False,
    )
    plt.title("SHAP Summary: Feature Impact on 30-Day Readmission Risk", fontsize=13, pad=15)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "shap_summary_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Saved: outputs/shap_summary_beeswarm.png")

    # 2. Global Bar Plot (Mean Absolute SHAP Values)
    logger.info("Generating SHAP Bar Plot...")
    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        shap_vals,
        X_test,
        plot_type="bar",
        max_display=max_display,
        show=False,
    )
    plt.title("Mean Absolute SHAP Values: Feature Importance for Readmission", fontsize=13, pad=15)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "shap_global_bar.png", dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Saved: outputs/shap_global_bar.png")

    # 3. Individual Patient Explanation (Waterfall Plot)
    # Select a patient who was predicted as high-risk for readmission
    logger.info("Generating SHAP Waterfall Plot for a high-risk patient...")
    proba = model.predict_proba(X_test)[:, 1]
    high_risk_idx = np.argmax(proba)

    shap_explanation = shap.Explanation(
        values=shap_vals[high_risk_idx],
        base_values=explainer.expected_value[1] if isinstance(explainer.expected_value, list) else explainer.expected_value,
        data=X_test.iloc[high_risk_idx].values,
        feature_names=X_test.columns.tolist(),
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.plots.waterfall(shap_explanation, max_display=max_display, show=False)
    plt.title(
        f"SHAP Waterfall: Why Patient #{high_risk_idx} Was Flagged High-Risk "
        f"(Predicted Probability: {proba[high_risk_idx]:.1%})",
        fontsize=11,
        pad=15,
    )
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "shap_waterfall_individual.png", dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Saved: outputs/shap_waterfall_individual.png")

    # 4. Dependence Plot (top feature vs readmission risk)
    logger.info("Generating SHAP Dependence Plot...")
    top_feature_idx = np.argmax(np.abs(shap_vals).mean(axis=0))
    top_feature_name = X_test.columns[top_feature_idx]

    fig, ax = plt.subplots(figsize=(8, 6))
    shap.dependence_plot(
        top_feature_idx,
        shap_vals,
        X_test,
        show=False,
        ax=ax,
    )
    ax.set_title(f"SHAP Dependence: {top_feature_name} vs Readmission Risk", fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "shap_dependence.png", dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Saved: outputs/shap_dependence.png")

    # Generate text summary for stakeholders
    _generate_stakeholder_summary(shap_vals, X_test, proba)

    logger.info("SHAP analysis complete.")


def _generate_stakeholder_summary(shap_vals, X_test, proba) -> None:
    """
    Writes a plain-English summary of the SHAP analysis for non-technical
    stakeholders such as hospital administrators and clinical leads.
    """
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    feature_importance = pd.Series(mean_abs_shap, index=X_test.columns).sort_values(ascending=False)

    top_5 = feature_importance.head(5)
    high_risk_count = (proba >= 0.5).sum()
    total = len(proba)

    summary_lines = [
        "=" * 70,
        "STAKEHOLDER BRIEFING: 30-Day Readmission Risk Model",
        "=" * 70,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"  The model identified {high_risk_count} out of {total} patients ({high_risk_count/total:.1%})",
        f"  in the test cohort as being at elevated risk of readmission within 30 days.",
        "",
        "TOP 5 DRIVERS OF READMISSION RISK",
        "-" * 40,
    ]

    for rank, (feature, importance) in enumerate(top_5.items(), 1):
        summary_lines.append(f"  {rank}. {feature} (Impact Score: {importance:.4f})")

    summary_lines.extend([
        "",
        "RECOMMENDED ACTIONS",
        "-" * 40,
        f"  - Prioritize discharge planning for patients with high {top_5.index[0]}.",
        f"  - Review cases where {top_5.index[1]} is a contributing factor.",
        "  - Consider post-discharge follow-up calls within 48 hours for flagged patients.",
        "  - Allocate care coordinator resources to the highest-risk cohort.",
        "",
        "NOTE: Full SHAP visualizations are available in the outputs/ directory.",
        "=" * 70,
    ])

    summary_text = "\n".join(summary_lines)

    summary_path = OUTPUT_DIR / "stakeholder_summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_text)

    logger.info(f"Saved: outputs/stakeholder_summary.txt")
    logger.info("\n" + summary_text)
