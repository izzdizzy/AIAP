"""
Model Evaluation Module for Chronic Condition Readmission Prediction
=====================================================================
Comprehensive model evaluation with detailed metrics, visualizations,
and healthcare-specific interpretations.

Singapore Healthcare Context:
- Evaluation metrics are interpreted in healthcare context
- Emphasis on recall to minimize missed high-risk patients
- Trade-off analysis between precision and recall for clinical decision-making
- SHAP integration for model explainability
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, average_precision_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
from typing import Dict, List, Tuple, Optional
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Set random seed for reproducibility
RANDOM_STATE = 42


class ModelEvaluator:
    """
    Comprehensive model evaluation with healthcare-specific interpretations.
    
    Generates:
    - Confusion Matrix
    - ROC Curve with AUC
    - Precision-Recall Curve
    - Classification Report
    - Metric comparisons
    - Healthcare context interpretations
    - Healthcare context interpretations
    - SHAP analysis for explainability
    def __init__(self, output_dir: str = 'results/evaluation'):
        """
        Initialize the model evaluator.
        
        Args:
            output_dir: Directory to save evaluation outputs
        """
        self.output_dir = output_dir
        self.evaluation_results = {}
        self.model_metrics = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def calculate_all_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                             y_pred_proba: np.ndarray = None) -> Dict:
        """
        Calculate comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional)
            
        Returns:
            Dict: All calculated metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_true, y_pred_proba) if y_pred_proba is not None else None,
            'average_precision': average_precision_score(y_true, y_pred_proba) if y_pred_proba is not None else None
        }
        
        return metrics
    
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray,
                             model_name: str = "Model", save_fig: bool = True) -> plt.Figure:
        """
        Plot confusion matrix with annotations.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            model_name: Name of the model
            save_fig: Whether to save the figure
            
        Returns:
            Figure object
        """
        logger.info(f"Plotting confusion matrix for {model_name}...")
        
        cm = confusion_matrix(y_true, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create heatmap
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Not Readmitted', 'Readmitted'],
                   yticklabels=['Not Readmitted', 'Readmitted'],
                   ax=ax, cbar_kws={'label': 'Count'},
                   annot_kws={'size': 14, 'weight': 'bold'})
        
        # Labels and title
        ax.set_xlabel('Predicted Label', fontsize=12, fontweight='bold')
        ax.set_ylabel('True Label', fontsize=12, fontweight='bold')
        ax.set_title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
        
        # Add counts as text
        tn, fp, fn, tp = cm.ravel()
        info_text = f"TN={tn}\nFP={fp}\nFN={fn}\nTP={tp}"
        fig.text(0.95, 0.02, info_text, ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_fig:
            plt.savefig(f'{self.output_dir}/confusion_matrix_{model_name.replace(" ", "_")}.png',
                       dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"✓ Saved confusion matrix to: {self.output_dir}/")
        else:
            plt.close()
        
        return fig
    
    def plot_roc_curve(self, y_true: np.ndarray, y_pred_proba: np.ndarray,
                      model_name: str = "Model", save_fig: bool = True) -> Tuple[plt.Figure, float]:
        """
        Plot ROC curve with AUC score.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            model_name: Name of the model
            save_fig: Whether to save the figure
            
        Returns:
            Tuple: (Figure object, AUC score)
        """
        logger.info(f"Plotting ROC curve for {model_name}...")
        
        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Plot ROC curve
        ax.plot(fpr, tpr, color='darkorange', lw=2,
               label=f'ROC Curve (AUC = {roc_auc:.4f})')
        
        # Plot diagonal line (random classifier)
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--',
               label='Random Classifier (AUC = 0.5)')
        
        # Formatting
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate', fontsize=12, fontweight='bold')
        ax.set_ylabel('True Positive Rate (Recall)', fontsize=12, fontweight='bold')
        ax.set_title(f'ROC Curve - {model_name}', fontsize=14, fontweight='bold')
        ax.legend(loc="lower right", fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Add threshold annotations (every 0.2)
        for i, thresh in enumerate(thresholds):
            if i % max(1, len(thresholds)//5) == 0:
                ax.annotate(f'{thresh:.2f}', (fpr[i], tpr[i]), fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        
        if save_fig:
            plt.savefig(f'{self.output_dir}/roc_curve_{model_name.replace(" ", "_")}.png',
                       dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"✓ Saved ROC curve to: {self.output_dir}/")
        else:
            plt.close()
        
        return fig, roc_auc
    
    def plot_precision_recall_curve(self, y_true: np.ndarray, y_pred_proba: np.ndarray,
                                   model_name: str = "Model", save_fig: bool = True) -> Tuple[plt.Figure, float]:
        """
        Plot Precision-Recall curve.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            model_name: Name of the model
            save_fig: Whether to save the figure
            
        Returns:
            Tuple: (Figure object, Average Precision score)
        """
        logger.info(f"Plotting Precision-Recall curve for {model_name}...")
        
        # Calculate PR curve
        precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
        avg_precision = average_precision_score(y_true, y_pred_proba)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Plot PR curve
        ax.plot(recall, precision, color='blue', lw=2,
               label=f'PR Curve (AP = {avg_precision:.4f})')
        
        # Formatting
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Recall (Sensitivity)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Precision', fontsize=12, fontweight='bold')
        ax.set_title(f'Precision-Recall Curve - {model_name}', fontsize=14, fontweight='bold')
        ax.legend(loc="lower left", fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_fig:
            plt.savefig(f'{self.output_dir}/pr_curve_{model_name.replace(" ", "_")}.png',
                       dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"✓ Saved PR curve to: {self.output_dir}/")
        else:
            plt.close()
        
        return fig, avg_precision
    
    def generate_classification_report(self, y_true: np.ndarray, y_pred: np.ndarray,
                                       model_name: str = "Model") -> str:
        """
        Generate detailed classification report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            model_name: Name of the model
            
        Returns:
            str: Formatted classification report
        """
        logger.info(f"Generating classification report for {model_name}...")
        
        report = classification_report(y_true, y_pred,
                                       target_names=['Not Readmitted', 'Readmitted'],
                                       digits=4,
                                       output_dict=False)
        
        # Save report to file
        report_path = f'{self.output_dir}/classification_report_{model_name.replace(" ", "_")}.txt'
        with open(report_path, 'w') as f:
            f.write(f"Classification Report - {model_name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)
        
        logger.info(f"✓ Saved classification report to: {report_path}")
        
        return report
    
    def interpret_metrics_for_healthcare(self, metrics: Dict, model_name: str = "Model") -> str:
        """
        Provide healthcare-specific interpretation of metrics.
        
        Args:
            metrics: Dictionary of evaluation metrics
            model_name: Name of the model
            
        Returns:
            str: Interpretation text
        """
        interpretation = []
        interpretation.append(f"\n{'='*80}")
        interpretation.append(f"HEALTHCARE INTERPRETATION - {model_name}")
        interpretation.append(f"{'='*80}\n")
        
        # Accuracy
        interpretation.append(f"📊 ACCURACY: {metrics['accuracy']:.2%}")
        interpretation.append(f"   Overall correctness: {metrics['accuracy']:.2%} of all predictions are correct.")
        interpretation.append(f"   ⚠️ In imbalanced medical data, accuracy alone can be misleading.\n")
        
        # Recall (Sensitivity) - MOST IMPORTANT FOR HEALTHCARE
        interpretation.append(f"🎯 RECALL (SENSITIVITY): {metrics['recall']:.2%}")
        interpretation.append(f"   Of all patients who WILL be readmitted, we correctly identified {metrics['recall']:.2%}.")
        interpretation.append(f"   MISSED CASES: {100 - metrics['recall']*100:.1f}% of readmitted patients were NOT flagged.")
        interpretation.append(f"   💡 HIGH RECALL IS CRITICAL: Missing a high-risk patient could lead to:")
        interpretation.append(f"       - Delayed intervention")
        interpretation.append(f"       - Worse health outcomes")
        interpretation.append(f"       - Higher healthcare costs\n")
        
        # Precision
        interpretation.append(f"🎯 PRECISION: {metrics['precision']:.2%}")
        interpretation.append(f"   Of all patients flagged as high-risk, {metrics['precision']:.2%} actually were readmitted.")
        interpretation.append(f"   FALSE ALARMS: {100 - metrics['precision']*100:.1f}% of flagged patients wouldn't have been readmitted.")
        interpretation.append(f"   💡 LOW PRECISION IMPACT:")
        interpretation.append(f"       - Unnecessary follow-up appointments")
        interpretation.append(f"       - Increased healthcare resource usage")
        interpretation.append(f"       - Potential patient anxiety\n")
        
        # F1-Score
        interpretation.append(f"⚖️ F1-SCORE: {metrics['f1_score']:.4f}")
        interpretation.append(f"   Harmonic mean of precision and recall.")
        interpretation.append(f"   Useful when you need a balance between recall and precision.\n")
        
        # ROC-AUC
        if metrics.get('roc_auc'):
            interpretation.append(f"📈 ROC-AUC: {metrics['roc_auc']:.4f}")
            interpretation.append(f"   Probability that the model ranks a random positive case higher than a random negative case.")
            interpretation.append(f"   {self._interpret_auc(metrics['roc_auc'])}\n")
        
        # Trade-off discussion
        interpretation.append(f"\n{'─'*80}")
        interpretation.append(f"TRADE-OFF ANALYSIS FOR SINGAPORE HEALTHCARE")
        interpretation.append(f"{'─'*80}")
        
        if metrics['recall'] > metrics['precision']:
            interpretation.append(f"✓ This model PRIORITIZES RECALL over precision.")
            interpretation.append(f"  GOOD FOR: Initial screening where missing cases is unacceptable.")
            interpretation.append(f"  RECOMMENDATION: Suitable for Singapore's primary care screening programs.")
        else:
            interpretation.append(f"⚠ This model PRIORITIZES PRECISION over recall.")
            interpretation.append(f"  CONCERN: May miss some high-risk patients.")
            interpretation.append(f"  RECOMMENDATION: Consider adjusting threshold or using a different model.")
        
        interpretation.append(f"\n💡 THRESHOLD RECOMMENDATION:")
        interpretation.append(f"   For chronic condition readmission prediction in Singapore:")
        interpretation.append(f"   • Use LOWER threshold to increase recall (catch more at-risk patients)")
        interpretation.append(f"   • Accept some false positives as cost of preventing readmissions")
        interpretation.append(f"   • Follow up flagged patients with additional clinical assessment\n")
        
        return '\n'.join(interpretation)
    
    def _interpret_auc(self, auc_score: float) -> str:
        """Provide qualitative interpretation of AUC score."""
        if auc_score >= 0.9:
            return "Excellent discrimination ability."
        elif auc_score >= 0.8:
            return "Good discrimination ability."
        elif auc_score >= 0.7:
            return "Fair discrimination ability."
        elif auc_score >= 0.6:
            return "Poor discrimination ability."
        else:
            return "Very poor discrimination - model needs improvement."
    
    def compare_models(self, models_metrics: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare multiple models side by side.
        
        Args:
            models_metrics: Dictionary mapping model names to their metrics
            
        Returns:
            pd.DataFrame: Comparison table
        """
        comparison_df = pd.DataFrame(models_metrics).T
        
        # Sort by ROC-AUC (or F1 if not available)
        sort_col = 'roc_auc' if 'roc_auc' in comparison_df.columns else 'f1_score'
        comparison_df = comparison_df.sort_values(sort_col, ascending=False)
        
        # Format as percentages
        for col in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']:
            if col in comparison_df.columns:
                comparison_df[col] = comparison_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
        
        return comparison_df
    
    def plot_model_comparison(self, models_metrics: Dict[str, Dict],
                             save_fig: bool = True) -> plt.Figure:
        """
        Create bar chart comparing model performances.
        
        Args:
            models_metrics: Dictionary of model metrics
            save_fig: Whether to save the figure
            
        Returns:
            Figure object
        """
        logger.info("Creating model comparison visualization...")
        
        # Convert to DataFrame
        df = pd.DataFrame(models_metrics).T
        
        # Select metrics to display
        metrics_to_show = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
        df_plot = df[[m for m in metrics_to_show if m in df.columns]].fillna(0)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Bar positions
        x = np.arange(len(df_plot))
        width = 0.8 / len(df_plot.columns)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(df_plot.columns)))
        
        for i, metric in enumerate(df_plot.columns):
            offset = (i - len(df_plot.columns)/2 + 0.5) * width
            ax.bar(x + offset, df_plot[metric], width, label=metric, color=colors[i])
        
        # Formatting
        ax.set_xlabel('Model', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(df_plot.index, rotation=45, ha='right')
        ax.legend(loc='lower right')
        ax.set_ylim([0, 1.05])
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_fig:
            plt.savefig(f'{self.output_dir}/model_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"✓ Saved model comparison to: {self.output_dir}/model_comparison.png")
        else:
            plt.close()
        
        return fig
    
    def evaluate_model_comprehensive(self, model, X_test: np.ndarray, y_test: np.ndarray,
                                    model_name: str = "Model",
                                    feature_names: List[str] = None) -> Dict:
        """
        Perform comprehensive evaluation of a single model.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model
            feature_names: Feature names for importance analysis
            
        Returns:
            Dict: Complete evaluation results
        """
        logger.info(f"\n{'='*80}")
        logger(f"COMPREHENSIVE EVALUATION: {model_name}")
        logger.info(f"{'='*80}")
        
        # Get predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = self.calculate_all_metrics(y_test, y_pred, y_pred_proba)
        
        # Store results
        self.model_metrics[model_name] = metrics
        
        # Generate visualizations
        self.plot_confusion_matrix(y_test, y_pred, model_name)
        
        if y_pred_proba is not None:
            self.plot_roc_curve(y_test, y_pred_proba, model_name)
            self.plot_precision_recall_curve(y_test, y_pred_proba, model_name)
        
        # Generate reports
        report = self.generate_classification_report(y_test, y_pred, model_name)
        interpretation = self.interpret_metrics_for_healthcare(metrics, model_name)
        
        # Feature importance (if available)
        feature_importance = None
        if feature_names is not None:
            if hasattr(model, 'feature_importances_'):
                importance_df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                feature_importance = importance_df
                
                # Plot feature importance
                self.plot_feature_importance(importance_df, model_name)
        
        # Compile results
        results = {
            'model_name': model_name,
            'metrics': metrics,
            'classification_report': report,
            'healthcare_interpretation': interpretation,
            'feature_importance': feature_importance
        }
        
        self.evaluation_results[model_name] = results
        
        # Print summary
        print(interpretation)
        
        return results
    
    def plot_feature_importance(self, importance_df: pd.DataFrame,
                               model_name: str = "Model",
                               top_n: int = 15,
                               save_fig: bool = True) -> plt.Figure:
        """
        Plot feature importance.
        
        Args:
            importance_df: DataFrame with features and importances
            model_name: Name of the model
            top_n: Number of top features to display
            save_fig: Whether to save the figure
            
        Returns:
            Figure object
        """
        logger.info(f"Plotting feature importance for {model_name}...")
        
        top_features = importance_df.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Horizontal bar chart
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(top_features)))
        bars = ax.barh(range(len(top_features)), top_features['importance'], color=colors)
        
        # Formatting
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['feature'], fontsize=10)
        ax.set_xlabel('Importance Score', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Feature Importance - {model_name}', fontsize=14, fontweight='bold')
        ax.invert_yaxis()  # Highest importance at top
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (idx, row) in enumerate(top_features.iterrows()):
            ax.text(row['importance'] + max(top_features['importance'])*0.01,
                   i, f"{row['importance']:.4f}", va='center', fontsize=9)
        
        plt.tight_layout()
        
        if save_fig:
            plt.savefig(f'{self.output_dir}/feature_importance_{model_name.replace(" ", "_")}.png',
                       dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"✓ Saved feature importance to: {self.output_dir}/")
        else:
            plt.close()
        
        return fig
    
    def save_evaluation_summary(self, results: Dict) -> None:
        """Save complete evaluation summary to file."""
        summary_path = f'{self.output_dir}/evaluation_summary.txt'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MODEL EVALUATION SUMMARY\n")
            f.write("Diabetes Readmission Prediction - Singapore Healthcare\n")
            f.write("=" * 80 + "\n\n")
            
            for model_name, result in results.items():
                f.write(f"\n{'='*60}\n")
                f.write(f"MODEL: {model_name}\n")
                f.write(f"{'='*60}\n\n")
                
                if 'metrics' in result:
                    f.write("METRICS:\n")
                    for metric, value in result['metrics'].items():
                        if value is not None:
                            f.write(f"  {metric}: {value:.4f}\n")
                
                if 'healthcare_interpretation' in result:
                    f.write("\n" + result['healthcare_interpretation'])
        
        logger.info(f"✓ Saved evaluation summary to: {summary_path}")


def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray,
                  model_name: str = "Model",
                  feature_names: List[str] = None,
                  output_dir: str = 'results/evaluation') -> Dict:
    """
    Convenience function for comprehensive model evaluation.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        model_name: Name of the model
        feature_names: Feature names
        output_dir: Output directory
        
    Returns:
        Dict: Evaluation results
    """
    evaluator = ModelEvaluator(output_dir)
    return evaluator.evaluate_model_comprehensive(model, X_test, y_test, model_name, feature_names)


if __name__ == "__main__":
    # Example usage with sample data
    print("Testing ModelEvaluator...")
    
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    
    # Create sample data
    np.random.seed(RANDOM_STATE)
    n_samples = 500
    
    X = np.random.randn(n_samples, 10)
    y = np.random.randint(0, 2, n_samples)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    # Train a simple model
    model = RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=10)
    model.fit(X_train, y_train)
    
    # Evaluate
    feature_names = [f'Feature_{i}' for i in range(X.shape[1])]
    
    try:
        results = evaluate_model(
            model, X_test, y_test,
            model_name="Random Forest Test",
            feature_names=feature_names
        )
        
        print("\n✓ Model evaluation test completed successfully!")
        print(f"Metrics: {results['metrics']}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
