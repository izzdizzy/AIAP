"""
Data Loading Module for Hospital Readmission Prediction - Chronic Conditions
=============================================================================
This module handles downloading, loading, and initial inspection of the patient dataset.

Singapore Healthcare Context:
- This dataset helps predict hospital readmissions for chronic condition patients
- Reducing readmissions can significantly reduce healthcare burden in Singapore
- Early identification of high-risk patients enables proactive care management
- Supports MOH Health 2020 goals for reducing avoidable readmissions by 15%
"""

import pandas as pd
import numpy as np
import os
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles loading and initial inspection of the chronic condition readmission dataset.
    
    Note: Uses diabetes patient data as a proxy, as diabetes is one of the most 
    prevalent chronic conditions in Singapore (11% of adults). The clinical features
    are representative of broader chronic disease management patterns.
    
    Attributes:
        data_path (str): Path to the dataset file
        df (pd.DataFrame): The loaded dataframe
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialize the DataLoader.
        
        Args:
            data_path: Path to the CSV file. If None, will look in default locations.
        """
        self.data_path = data_path
        self.df = None
        self.raw_df = None
        
    def load_from_url(self, url: str = None) -> pd.DataFrame:
        """
        Load dataset from UCI repository or local file.
        
        Args:
            url: Direct URL to the dataset (optional)
            
        Returns:
            pd.DataFrame: Loaded dataset
            
        Note:
            The UCI Diabetes dataset contains 100,000+ patient records from 
            130 US hospitals (1999-2008). While not Singapore-specific, the 
            clinical features (medications, lab procedures, length of stay) are representative of broader chronic disease management patterns.
        """
        if url is None:
            # Default to local file if available
            local_paths = [
                'data/raw/diabetes_data_upload.csv',
                'data/raw/diabetes_130_all_discharges.csv',
                '../data/raw/diabetes_data_upload.csv'
            ]
            for path in local_paths:
                if os.path.exists(path):
                    self.data_path = path
                    logger.info(f"Found local dataset at: {path}")
                    return self.load_from_csv()
            
            # If no local file, provide instructions
            logger.warning("""
            Dataset not found locally. Please download from:
            https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
            
            Save as: data/raw/diabetes_data_upload.csv
            """)
            return None
        
        try:
            logger.info(f"Loading dataset from URL: {url}")
            self.df = pd.read_csv(url)
            self.raw_df = self.df.copy()
            logger.info(f"Successfully loaded {len(self.df)} records")
            return self.df
        except Exception as e:
            logger.error(f"Error loading from URL: {e}")
            return None
    
    def load_from_csv(self, filepath: str = None) -> pd.DataFrame:
        """
        Load dataset from local CSV file.
        
        Args:
            filepath: Path to CSV file (uses instance path if None)
            
        Returns:
            pd.DataFrame: Loaded dataset
        """
        if filepath is None:
            filepath = self.data_path
            
        if filepath is None:
            raise FileNotFoundError("No data path specified")
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset not found at: {filepath}")
        
        logger.info(f"Loading dataset from: {filepath}")
        
        try:
            # Try loading with default settings
            self.df = pd.read_csv(filepath)
            self.raw_df = self.df.copy()
            logger.info(f"✓ Successfully loaded {len(self.df):,} records with {len(self.df.columns)} features")
            return self.df
        except Exception as e:
            logger.warning(f"Standard load failed: {e}, trying alternative encoding...")
            try:
                self.df = pd.read_csv(filepath, encoding='latin-1')
                self.raw_df = self.df.copy()
                logger.info(f"✓ Successfully loaded with latin-1 encoding")
                return self.df
            except Exception as e2:
                logger.error(f"Failed to load dataset: {e2}")
                raise
    
    def get_dataset_info(self) -> dict:
        """
        Get comprehensive information about the dataset.
        
        Returns:
            dict: Dictionary containing dataset metadata
        """
        if self.df is None:
            raise ValueError("No dataset loaded. Call load_from_csv() first.")
        
        info = {
            'shape': self.df.shape,
            'n_samples': len(self.df),
            'n_features': len(self.df.columns),
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'memory_usage': f"{self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
            'target_column': 'readmitted',
            'description': """
            UCI Diabetes 130-US Hospitals Dataset (1999-2008)
            - Contains patient records for chronic condition admissions (diabetes as proxy)
            - Target: 30-day hospital readmission (YES/NO)
            - Features include demographics, diagnoses, medications, lab procedures
            - Adapted for Singapore healthcare context to improve patient outcomes
            """
        }
        return info
    
    def display_overview(self) -> None:
        """Print a comprehensive overview of the dataset."""
        if self.df is None:
            print("No dataset loaded.")
            return
        
        print("=" * 80)
        print("HOSPITAL READMISSION PREDICTION FOR CHRONIC CONDITIONS - DATASET OVERVIEW")
        print("=" * 80)
        print(f"\n📊 Dataset Shape: {self.df.shape[0]:,} samples × {self.df.shape[1]} features")
        print(f"\n💾 Memory Usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print("\n📋 Column Names:")
        for i, col in enumerate(self.df.columns, 1):
            print(f"   {i}. {col}")
        print("\n🔢 Data Types:")
        print(self.df.dtypes.to_string())
        print("\n🎯 Target Variable Distribution:")
        if 'readmitted' in self.df.columns:
            print(self.df['readmitted'].value_counts().to_string())
        print("=" * 80)
    
    def save_processed_data(self, output_path: str = 'data/processed/cleaned_data.csv') -> None:
        """
        Save the loaded data for further processing.
        
        Args:
            output_path: Path to save the processed data
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_csv(output_path, index=False)
        logger.info(f"✓ Saved data to: {output_path}")


def load_chronic_condition_dataset(data_path: str = 'data/raw/diabetes_data_upload.csv') -> pd.DataFrame:
    """
    Convenience function to load the chronic condition readmission dataset.
    
    Note: Uses diabetes data as proxy for chronic conditions due to its prevalence
    and well-documented clinical patterns that generalize across chronic diseases.
    
    Args:
        data_path: Path to the dataset CSV file
        
    Returns:
        pd.DataFrame: Loaded dataset
    """
    loader = DataLoader(data_path)
    return loader.load_from_csv()


if __name__ == "__main__":
    # Example usage
    print("Testing DataLoader...")
    loader = DataLoader()
    
    # Try to load from default location
    try:
        df = loader.load_from_csv('data/raw/diabetes_data_upload.csv')
        loader.display_overview()
        
        info = loader.get_dataset_info()
        print(f"\nTarget column: {info['target_column']}")
        print(f"Description: {info['description']}")
    except FileNotFoundError as e:
        print(f"Dataset not found: {e}")
        print("\nPlease download the dataset from:")
        print("https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008")
        print("\nSave it as: data/raw/diabetes_data_upload.csv")
