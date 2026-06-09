"""
Exploratory Data Analysis (EDA) Module for Diabetes Readmission Prediction
==========================================================================
Comprehensive EDA with visualizations to understand patterns in chronic condition readmissions.

Singapore Healthcare Context:
- Understanding readmission patterns helps optimize hospital resource allocation
- Identifies high-risk patient groups for targeted interventions
- Supports evidence-based healthcare policy decisions in Singapore
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, List, Optional
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


class EDAAnalyzer:
    """
    Comprehensive Exploratory Data Analysis for chronic condition readmission dataset (diabetes as proxy).
    
    Generates insightful visualizations and statistical summaries to understand
    patterns related to hospital readmissions.
    """
    
    def __init__(self, df: pd.DataFrame, output_dir: str = 'results/eda'):
        """
        Initialize the EDA Analyzer.
        
        Args:
            df: Pandas DataFrame with the dataset
            output_dir: Directory to save visualization outputs
        """
        self.df = df.copy()
        self.output_dir = output_dir
        self.numeric_cols = []
        self.categorical_cols = []
        self.target_col = 'readmitted'
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Identify column types
        self._identify_column_types()
    
    def _identify_column_types(self) -> None:
        """Identify numeric and categorical columns."""
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = self.df.select_dtypes(include=['object']).columns.tolist()
        
        # Remove target from feature lists if present
        if self.target_col in self.numeric_cols:
            self.numeric_cols.remove(self.target_col)
        if self.target_col in self.categorical_cols:
            self.categorical_cols.remove(self.target_col)
    
    def generate_full_report(self, save_figs: bool = True) -> dict:
        """
        Generate comprehensive EDA report with all visualizations.
        
        Args:
            save_figs: Whether to save figures to disk
            
        Returns:
            dict: Summary statistics and findings
        """
        print("=" * 80)
        print("COMPREHENSIVE EXPLORATORY DATA ANALYSIS REPORT")
        print("=" * 80)
        
        report = {
            'dataset_overview': self.dataset_overview(),
            'missing_value_analysis': self.analyze_missing_values(save_figs),
            'target_distribution': self.analyze_target_variable(save_figs),
            'numeric_distributions': self.analyze_numeric_features(save_figs),
            'categorical_distributions': self.analyze_categorical_features(save_figs),
            'correlation_analysis': self.analyze_correlations(save_figs),
            'feature_vs_target': self.analyze_features_vs_target(save_figs),
            'statistical_summary': self.get_statistical_summary(),
            'key_insights': self.generate_insights()
        }
        
        if save_figs:
            self._save_report_summary(report)
        
        return report
    
    def dataset_overview(self) -> dict:
        """Display basic dataset information."""
        print("\n" + "=" * 80)
        print("1. DATASET OVERVIEW")
        print("=" * 80)
        
        overview = {
            'shape': self.df.shape,
            'n_samples': len(self.df),
            'n_features': len(self.df.columns),
            'n_numeric': len(self.numeric_cols),
            'n_categorical': len(self.categorical_cols),
            'columns': self.df.columns.tolist(),
            'memory_mb': self.df.memory_usage(deep=True).sum() / 1024**2
        }
        
        print(f"\n📊 Dataset Dimensions: {overview['n_samples']:,} samples × {overview['n_features']} features")
        print(f"🔢 Numeric Features: {overview['n_numeric']}")
        print(f"📝 Categorical Features: {overview['n_categorical']}")
        print(f"💾 Memory Usage: {overview['memory_mb']:.2f} MB")
        
        return overview
    
    def analyze_missing_values(self, save_figs: bool = True) -> dict:
        """
        Analyze and visualize missing values in the dataset.
        
        Args:
            save_figs: Whether to save the visualization
            
        Returns:
            dict: Missing value statistics
        """
        print("\n" + "=" * 80)
        print("2. MISSING VALUE ANALYSIS")
        print("=" * 80)
        
        # Calculate missing values
        missing = self.df.isnull().sum()
        missing_percent = (missing / len(self.df) * 100).round(2)
        missing_df = pd.DataFrame({
            'Missing Count': missing,
            'Missing Percentage': missing_percent
        }).sort_values('Missing Count', ascending=False)
        
        # Filter columns with missing values
        missing_df = missing_df[missing_df['Missing Count'] > 0]
        
        print(f"\nColumns with missing values: {len(missing_df)}")
        if len(missing_df) > 0:
            print("\nTop 10 columns with missing values:")
            print(missing_df.head(10).to_string())
        
        # Create visualizations
        if len(missing_df) > 0 and save_figs:
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            
            # Bar chart of missing values
            top_missing = missing_df.head(15)
            axes[0].barh(range(len(top_missing)), top_missing['Missing Count'], color='coral')
            axes[0].set_yticks(range(len(top_missing)))
            axes[0].set_yticklabels(top_missing.index)
            axes[0].set_xlabel('Missing Count')
            axes[0].set_title('Missing Values by Column (Top 15)', fontweight='bold')
            axes[0].invert_yaxis()
            
            # Heatmap of missing values
            missing_matrix = self.df[missing_df.index[:20]].isnull()
            sns.heatmap(missing_matrix, cmap='YlOrRd', ax=axes[1], cbar_kws={'label': 'Missing'})
            axes[1].set_title('Missing Value Pattern (Heatmap)', fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/01_missing_values.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"\n✓ Saved: 01_missing_values.png")
        
        return {
            'columns_with_missing': len(missing_df),
            'total_missing': missing.sum(),
            'missing_details': missing_df.to_dict()
        }
    
    def analyze_target_variable(self, save_figs: bool = True) -> dict:
        """
        Analyze the distribution of the target variable (readmitted).
        
        Args:
            save_figs: Whether to save the visualization
            
        Returns:
            dict: Target variable statistics
        """
        print("\n" + "=" * 80)
        print("3. TARGET VARIABLE DISTRIBUTION")
        print("=" * 80)
        
        if self.target_col not in self.df.columns:
            print("⚠️ Target column not found!")
            return {}
        
        target_dist = self.df[self.target_col].value_counts()
        target_pct = (self.df[self.target_col].value_counts(normalize=True) * 100).round(2)
        
        print(f"\n🎯 Target Variable: '{self.target_col}'")
        print("\nDistribution:")
        for val, count in target_dist.items():
            pct = target_pct[val]
            print(f"   {val}: {count:,} ({pct}%)")
        
        # Check for class imbalance
        if len(target_dist) == 2:
            ratio = target_dist.iloc[0] / target_dist.iloc[1]
            print(f"\n⚖️ Class Imbalance Ratio: {ratio:.2f}:1")
            if ratio > 2 or ratio < 0.5:
                print("   ⚠️ Significant class imbalance detected - will need handling!")
        
        # Visualization
        if save_figs:
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Bar chart
            colors = ['steelblue', 'coral']
            axes[0].bar(target_dist.index.astype(str), target_dist.values, color=colors, edgecolor='black', linewidth=1.5)
            axes[0].set_xlabel('Readmission Status', fontsize=12)
            axes[0].set_ylabel('Count', fontsize=12)
            axes[0].set_title('Distribution of Hospital Readmissions', fontweight='bold', fontsize=14)
            
            # Add percentage labels
            for i, (idx, val) in enumerate(target_dist.items()):
                axes[0].text(i, val + max(target_dist.values)*0.02, f'{target_pct[idx]:.1f}%', 
                           ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            # Pie chart
            axes[1].pie(target_dist.values, labels=target_dist.index.astype(str), autopct='%1.1f%%',
                       colors=colors, explode=[0.05] * len(target_dist), shadow=True)
            axes[1].set_title('Readmission Proportion', fontweight='bold', fontsize=14)
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/02_target_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"\n✓ Saved: 02_target_distribution.png")
        
        return {
            'distribution': target_dist.to_dict(),
            'percentages': target_pct.to_dict(),
            'is_imbalanced': len(target_dist) == 2 and (target_dist.iloc[0] / target_dist.iloc[1] > 2 or target_dist.iloc[0] / target_dist.iloc[1] < 0.5)
        }
    
    def analyze_numeric_features(self, save_figs: bool = True) -> dict:
        """
        Analyze distributions of numeric features.
        
        Args:
            save_figs: Whether to save the visualizations
            
        Returns:
            dict: Numeric feature statistics
        """
        print("\n" + "=" * 80)
        print("4. NUMERIC FEATURE DISTRIBUTIONS")
        print("=" * 80)
        
        key_numeric = ['time_in_hospital', 'num_lab_procedures', 'num_procedures', 
                      'num_medications', 'number_diagnoses', 'age']
        available_numeric = [col for col in key_numeric if col in self.df.columns]
        
        if not available_numeric:
            available_numeric = self.numeric_cols[:6]
        
        print(f"\nAnalyzing {len(available_numeric)} key numeric features...")
        
        # Create distribution plots
        if save_figs and len(available_numeric) > 0:
            n_cols = 3
            n_rows = (len(available_numeric) + n_cols - 1) // n_cols
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5*n_rows))
            axes = axes.flatten() if n_rows > 1 else [axes] if len(available_numeric) == 1 else axes
            
            for i, col in enumerate(available_numeric):
                if col in self.df.columns:
                    data = self.df[col].dropna()
                    axes[i].hist(data, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
                    axes[i].axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.1f}')
                    axes[i].axvline(data.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {data.median():.1f}')
                    axes[i].set_xlabel(col, fontsize=11)
                    axes[i].set_ylabel('Frequency', fontsize=11)
                    axes[i].set_title(f'Distribution of {col}', fontweight='bold', fontsize=12)
                    axes[i].legend(fontsize=9)
                    axes[i].grid(True, alpha=0.3)
            
            # Hide empty subplots
            for j in range(len(available_numeric), len(axes)):
                axes[j].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/03_numeric_distributions.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 03_numeric_distributions.png")
        
        # Box plots for outlier detection
        if save_figs and len(available_numeric) > 0:
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            axes = axes.flatten()
            
            for i, col in enumerate(available_numeric[:6]):
                if col in self.df.columns:
                    sns.boxplot(y=self.df[col], ax=axes[i], color='lightcoral')
                    axes[i].set_title(f'Box Plot: {col}', fontweight='bold', fontsize=12)
                    axes[i].set_ylabel('Value')
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/04_numeric_boxplots.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 04_numeric_boxplots.png")
        
        # Statistical summary
        stats = self.df[available_numeric].describe()
        print("\nStatistical Summary:")
        print(stats.to_string())
        
        return {'statistics': stats.to_dict(), 'features_analyzed': available_numeric}
    
    def analyze_categorical_features(self, save_figs: bool = True) -> dict:
        """
        Analyze distributions of categorical features.
        
        Args:
            save_figs: Whether to save the visualizations
            
        Returns:
            dict: Categorical feature statistics
        """
        print("\n" + "=" * 80)
        print("5. CATEGORICAL FEATURE DISTRIBUTIONS")
        print("=" * 80)
        
        key_categorical = ['gender', 'race', 'admission_type_id', 'discharge_disposition_id',
                          'payer_code', 'diabetesMed', 'change', 'insulin']
        available_cat = [col for col in key_categorical if col in self.df.columns]
        
        if not available_cat:
            available_cat = self.categorical_cols[:6]
        
        print(f"\nAnalyzing {len(available_cat)} key categorical features...")
        
        # Create bar plots for top categories
        if save_figs and len(available_cat) > 0:
            n_cols = 2
            n_rows = (len(available_cat) + n_cols - 1) // n_cols
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 5*n_rows))
            axes = axes.flatten() if n_rows > 1 else [axes] if len(available_cat) == 1 else axes
            
            for i, col in enumerate(available_cat):
                if col in self.df.columns:
                    # Get top 10 categories
                    top_categories = self.df[col].value_counts().head(10)
                    colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))
                    
                    axes[i].bar(range(len(top_categories)), top_categories.values, color=colors, edgecolor='black')
                    axes[i].set_xticks(range(len(top_categories)))
                    axes[i].set_xticklabels([str(x)[:15] for x in top_categories.index], rotation=45, ha='right')
                    axes[i].set_xlabel('Category', fontsize=11)
                    axes[i].set_ylabel('Count', fontsize=11)
                    axes[i].set_title(f'Top Categories: {col}', fontweight='bold', fontsize=12)
                    axes[i].grid(True, alpha=0.3, axis='y')
            
            # Hide empty subplots
            for j in range(len(available_cat), len(axes)):
                axes[j].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/05_categorical_distributions.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 05_categorical_distributions.png")
        
        return {'features_analyzed': available_cat}
    
    def analyze_correlations(self, save_figs: bool = True) -> dict:
        """
        Analyze correlations between numeric features.
        
        Args:
            save_figs: Whether to save the visualizations
            
        Returns:
            dict: Correlation analysis results
        """
        print("\n" + "=" * 80)
        print("6. CORRELATION ANALYSIS")
        print("=" * 80)
        
        # Select numeric columns for correlation
        numeric_data = self.df[self.numeric_cols].select_dtypes(include=[np.number])
        
        if len(numeric_data.columns) == 0:
            print("No numeric columns for correlation analysis.")
            return {}
        
        corr_matrix = numeric_data.corr()
        print(f"\nCorrelation matrix shape: {corr_matrix.shape}")
        
        # Identify strong correlations
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                if abs(corr_matrix.iloc[i, j]) > 0.5:
                    strong_corr.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_matrix.iloc[i, j]
                    })
        
        if strong_corr:
            print(f"\n🔗 Strong correlations (|r| > 0.5): {len(strong_corr)}")
            for corr in strong_corr[:5]:
                print(f"   {corr['feature1']} ↔ {corr['feature2']}: r = {corr['correlation']:.3f}")
        
        # Visualization
        if save_figs:
            fig, axes = plt.subplots(1, 2, figsize=(18, 7))
            
            # Full correlation heatmap
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, cmap='coolwarm', annot=False, 
                       center=0, square=True, ax=axes[0], cbar_kws={'shrink': 0.8})
            axes[0].set_title('Feature Correlation Heatmap (Upper Triangle)', fontweight='bold', fontsize=14)
            
            # Top correlations (absolute values)
            if len(corr_matrix.columns) > 1:
                # Get absolute correlation values
                corr_abs = corr_matrix.abs()
                # Get upper triangle
                mask_upper = np.triu(np.ones_like(corr_abs, dtype=bool), k=1)
                corr_flat = corr_abs.where(mask_upper).stack().sort_values(ascending=False)
                
                if len(corr_flat) > 0:
                    top_n = min(15, len(corr_flat))
                    top_corr = corr_flat.head(top_n)
                    
                    colors = ['coral' if corr_matrix.loc[idx[0], idx[1]] > 0 else 'steelblue' 
                             for idx in top_corr.index]
                    
                    axes[1].barh(range(len(top_corr)), top_corr.values, color=colors)
                    axes[1].set_yticks(range(len(top_corr)))
                    axes[1].set_yticklabels([f"{idx[0]} vs {idx[1]}" for idx in top_corr.index], fontsize=9)
                    axes[1].set_xlabel('Absolute Correlation', fontsize=12)
                    axes[1].set_title(f'Top {top_n} Strongest Correlations', fontweight='bold', fontsize=14)
                    axes[1].grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/06_correlation_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"\n✓ Saved: 06_correlation_analysis.png")
        
        return {
            'correlation_matrix': corr_matrix,
            'strong_correlations': strong_corr
        }
    
    def analyze_features_vs_target(self, save_figs: bool = True) -> dict:
        """
        Analyze relationships between features and target variable.
        
        Args:
            save_figs: Whether to save the visualizations
            
        Returns:
            dict: Feature-target relationship analysis
        """
        print("\n" + "=" * 80)
        print("7. FEATURE RELATIONSHIPS WITH READMISSION STATUS")
        print("=" * 80)
        
        if self.target_col not in self.df.columns:
            print("Target column not found!")
            return {}
        
        # Convert target to binary for analysis
        target_binary = self.df[self.target_col].map({'YES': 1, 'NO': 0, '<30': 1, '>30': 0}).fillna(0)
        
        analyzed_features = []
        
        # Numeric features vs target
        key_features = ['time_in_hospital', 'num_lab_procedures', 'num_medications', 
                       'number_diagnoses', 'age', 'num_procedures']
        available_features = [col for col in key_features if col in self.df.columns]
        
        if save_figs and len(available_features) > 0:
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            axes = axes.flatten()
            
            for i, col in enumerate(available_features[:6]):
                if col in self.df.columns:
                    # Create boxplot comparing feature values for readmitted vs non-readmitted
                    df_plot = self.df[[col, self.target_col]].dropna()
                    df_plot['readmit_binary'] = df_plot[self.target_col].map({'YES': 1, 'NO': 0, '<30': 1, '>30': 0}).fillna(0)
                    
                    sns.boxplot(x='readmit_binary', y=col, data=df_plot, ax=axes[i], 
                               palette=['lightgreen', 'salmon'])
                    axes[i].set_xlabel('Readmitted (1=YES, 0=NO)', fontsize=11)
                    axes[i].set_ylabel(col, fontsize=11)
                    axes[i].set_title(f'{col} by Readmission Status', fontweight='bold', fontsize=12)
                    axes[i].set_xticks([0, 1])
                    axes[i].set_xticklabels(['No', 'Yes'])
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/07_features_vs_target.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 07_features_vs_target.png")
        
        # Additional: Age distribution by readmission
        if 'age' in self.df.columns and save_figs:
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Histogram comparison
            readmitted = self.df[self.df[self.target_col].isin(['YES', '<30'])]['age'].dropna()
            not_readmitted = self.df[self.df[self.target_col].isin(['NO', '>30'])]['age'].dropna()
            
            axes[0].hist(readmitted, bins=20, alpha=0.6, color='salmon', label='Readmitted', edgecolor='black')
            axes[0].hist(not_readmitted, bins=20, alpha=0.6, color='lightgreen', label='Not Readmitted', edgecolor='black')
            axes[0].set_xlabel('Age', fontsize=12)
            axes[0].set_ylabel('Frequency', fontsize=12)
            axes[0].set_title('Age Distribution by Readmission Status', fontweight='bold', fontsize=14)
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # Violin plot
            df_violin = self.df[['age', self.target_col]].dropna()
            df_violin['readmit_binary'] = df_violin[self.target_col].map({'YES': 1, 'NO': 0, '<30': 1, '>30': 0}).fillna(0)
            sns.violinplot(x='readmit_binary', y='age', data=df_violin, ax=axes[1], palette=['lightgreen', 'salmon'])
            axes[1].set_xlabel('Readmitted (1=YES, 0=NO)', fontsize=12)
            axes[1].set_ylabel('Age', fontsize=12)
            axes[1].set_title('Age Distribution (Violin Plot)', fontweight='bold', fontsize=14)
            axes[1].set_xticks([0, 1])
            axes[1].set_xticklabels(['No', 'Yes'])
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/08_age_vs_readmission.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 08_age_vs_readmission.png")
        
        # Time in hospital analysis
        if 'time_in_hospital' in self.df.columns and save_figs:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            df_time = self.df[['time_in_hospital', self.target_col]].dropna()
            df_time['readmit_binary'] = df_time[self.target_col].map({'YES': 1, 'NO': 0, '<30': 1, '>30': 0}).fillna(0)
            
            sns.boxplot(x='readmit_binary', y='time_in_hospital', data=df_time, ax=ax, palette=['lightgreen', 'salmon'])
            ax.set_xlabel('Readmitted (1=YES, 0=NO)', fontsize=12)
            ax.set_ylabel('Time in Hospital (days)', fontsize=12)
            ax.set_title('Length of Hospital Stay by Readmission Status', fontweight='bold', fontsize=14)
            ax.set_xticks([0, 1])
            ax.set_xticklabels(['No', 'Yes'])
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/09_time_in_hospital_vs_readmission.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: 09_time_in_hospital_vs_readmission.png")
        
        return {'features_analyzed': available_features}
    
    def get_statistical_summary(self) -> dict:
        """Get comprehensive statistical summary of the dataset."""
        print("\n" + "=" * 80)
        print("8. STATISTICAL SUMMARY")
        print("=" * 80)
        
        summary = {
            'numeric_stats': self.df[self.numeric_cols].describe().to_dict(),
            'categorical_stats': {}
        }
        
        print("\nNumeric Features Statistics:")
        print(self.df[self.numeric_cols].describe().to_string())
        
        # Categorical stats
        for col in self.categorical_cols[:5]:
            summary['categorical_stats'][col] = {
                'unique_count': self.df[col].nunique(),
                'most_common': self.df[col].mode().iloc[0] if len(self.df[col].mode()) > 0 else None,
                'most_common_freq': self.df[col].value_counts().iloc[0] if len(self.df[col].value_counts()) > 0 else 0
            }
        
        print("\nCategorical Features (sample):")
        for col in self.categorical_cols[:5]:
            print(f"\n{col}:")
            print(f"   Unique values: {self.df[col].nunique()}")
            print(f"   Most common: {self.df[col].mode().iloc[0] if len(self.df[col].mode()) > 0 else 'N/A'}")
        
        return summary
    
    def generate_insights(self) -> List[str]:
        """Generate key insights from the EDA."""
        print("\n" + "=" * 80)
        print("9. KEY INSIGHTS & OBSERVATIONS")
        print("=" * 80)
        
        insights = []
        
        # Target distribution insight
        if self.target_col in self.df.columns:
            target_dist = self.df[self.target_col].value_counts(normalize=True)
            readmit_rate = target_dist.get('YES', 0) + target_dist.get('<30', 0)
            insights.append(f"📊 Readmission Rate: {readmit_rate*100:.1f}% of patients are readmitted within 30 days")
            print(f"\n✓ Readmission Rate: {readmit_rate*100:.1f}%")
        
        # Numeric feature insights
        if 'time_in_hospital' in self.df.columns:
            mean_stay = self.df['time_in_hospital'].mean()
            insights.append(f"🏥 Average Hospital Stay: {mean_stay:.1f} days")
            print(f"✓ Average Hospital Stay: {mean_stay:.1f} days")
        
        if 'age' in self.df.columns:
            age_groups = pd.cut(self.df['age'].dropna(), bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
            most_common_age = age_groups.mode()
            if len(most_common_age) > 0:
                insights.append(f"👴 Most Common Age Group: {most_common_age.iloc[0]}")
                print(f"✓ Most Common Age Group: {most_common_age.iloc[0]}")
        
        # Missing data insight
        missing_pct = (self.df.isnull().sum() / len(self.df) * 100).sum() / len(self.df.columns)
        insights.append(f"⚠️ Average Missing Data per Column: {missing_pct:.1f}%")
        print(f"✓ Average Missing Data: {missing_pct:.1f}% per column")
        
        # Healthcare implications
        insights.append("\n🇸🇬 SINGAPORE HEALTHCARE IMPLICATIONS:")
        insights.append("   • Early identification of high-risk patients can reduce hospital burden")
        insights.append("   • Predictive model enables proactive care management")
        insights.append("   • Resource optimization for Singapore's healthcare system")
        insights.append("   • Improved patient outcomes through timely interventions")
        
        print("\n🇸🇬 SINGAPORE HEALTHCARE IMPLICATIONS:")
        print("   • Early identification of high-risk patients can reduce hospital burden")
        print("   • Predictive model enables proactive care management")
        print("   • Resource optimization for Singapore's healthcare system")
        print("   • Improved patient outcomes through timely interventions")
        
        return insights
    
    def _save_report_summary(self, report: dict) -> None:
        """Save a text summary of the EDA report."""
        summary_path = f'{self.output_dir}/eda_summary.txt'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EXPLORATORY DATA ANALYSIS SUMMARY\n")
            f.write("Diabetes Readmission Prediction - Singapore Healthcare\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Dataset Shape: {report['dataset_overview']['shape']}\n")
            f.write(f"Numeric Features: {report['dataset_overview']['n_numeric']}\n")
            f.write(f"Categorical Features: {report['dataset_overview']['n_categorical']}\n\n")
            
            f.write("KEY INSIGHTS:\n")
            f.write("-" * 40 + "\n")
            for insight in report['key_insights']:
                f.write(f"{insight}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("Visualizations saved to: " + self.output_dir + "/\n")
        
        logger.info(f"✓ Saved EDA summary to: {summary_path}")


def run_eda(df: pd.DataFrame, output_dir: str = 'results/eda', save_figs: bool = True) -> dict:
    """
    Convenience function to run complete EDA.
    
    Args:
        df: Input DataFrame
        output_dir: Directory to save outputs
        save_figs: Whether to save figures
        
    Returns:
        dict: EDA report
    """
    analyzer = EDAAnalyzer(df, output_dir)
    return analyzer.generate_full_report(save_figs)


if __name__ == "__main__":
    # Example usage
    print("Testing EDA Analyzer...")
    
    # Create sample data for testing
    np.random.seed(RANDOM_STATE)
    n_samples = 1000
    
    sample_df = pd.DataFrame({
        'age': np.random.choice(['10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80'], n_samples),
        'time_in_hospital': np.random.randint(1, 14, n_samples),
        'num_lab_procedures': np.random.randint(1, 100, n_samples),
        'num_medications': np.random.randint(1, 50, n_samples),
        'number_diagnoses': np.random.randint(1, 10, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'readmitted': np.random.choice(['YES', 'NO'], n_samples, p=[0.3, 0.7])
    })
    
    print(f"Created sample dataset with {len(sample_df)} records")
    
    # Run EDA on sample data
    try:
        report = run_eda(sample_df, output_dir='results/eda_test', save_figs=True)
        print("\n✓ EDA completed successfully!")
        print(f"Key insights generated: {len(report['key_insights'])}")
    except Exception as e:
        print(f"Error running EDA: {e}")
