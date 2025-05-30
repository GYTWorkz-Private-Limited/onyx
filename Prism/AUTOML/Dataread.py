import pandas as pd
import dask.dataframe as dd
import os
import great_expectations as ge
import logging
from pathlib import Path
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_file_hash(file_path):
    """Calculate file hash for versioning."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def validate_schema(df, file_path):
    """Perform basic schema validation using Great Expectations."""
    try:
        ge_df = ge.from_pandas(df)
        for col in df.columns:
            result = ge_df.expect_column_values_to_not_be_null(col)
            if not result["success"]:
                logger.warning(f"Column {col} contains null values")
        logger.info("Schema validation completed")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")

def summarize_data(df):
    """Print dataset summary including shape, columns, nulls, uniques, and describe."""
    try:
        if isinstance(df, dd.DataFrame):
            logger.info("Computing Dask DataFrame summary (may take time)...")
            df = df.compute()

        print("\ Data Summary:")
        print(f"Shape: {df.shape}")
        # print(f"Column Names: {list(df.columns)}\n")

        print(" Unique Values Per Column:")
        for col in df.columns:
            print(f"  {col}: {df[col].nunique()} unique values")

        null_cols = df.isnull().sum()
        print("\n Columns with Missing Values:")
        print(null_cols[null_cols > 0])

        print("\n Descriptive Statistics:")
        print(df.describe(include='all'))

    except Exception as e:
        logger.error(f"Failed during data summarization: {e}")

def read_dataset(file_path, large_dataset_threshold=1_000_000):
    """
    Read dataset from file path, handling various formats and sizes.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        logger.info(f"Reading file: {file_path} (Extension: {file_ext})")
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")

        is_large = file_size_mb > 100
        import csv
        def detect_delimiter(file_path):
            with open(file_path, 'r') as f:
                sample = f.read(2048)
                sniffer = csv.Sniffer()
                return sniffer.sniff(sample).delimiter


        if file_ext in [".csv", ".txt"]:
            delimiter = detect_delimiter(file_path)
            df = dd.read_csv(file_path, sep=delimiter) if is_large else pd.read_csv(file_path, sep=delimiter)

        # if file_ext in [".csv", ".txt"]:
        #     df = dd.read_csv(file_path) if is_large else pd.read_csv(file_path)
        elif file_ext in [".xlsx", ".xls"]:
            logger.warning("Excel files not supported with Dask; using Pandas")
            df = pd.read_excel(file_path, engine="openpyxl")
        elif file_ext == ".json":
            df = dd.read_json(file_path) if is_large else pd.read_json(file_path)
        elif file_ext == ".parquet":
            df = dd.read_parquet(file_path) if is_large else pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")

        metadata = {
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "file_hash": get_file_hash(file_path),
            "row_count": len(df) if isinstance(df, pd.DataFrame) else df.shape[0].compute(),
            "columns": list(df.columns)
        }
        logger.info(f"Dataset metadata: {json.dumps(metadata, indent=2)}")

        if isinstance(df, pd.DataFrame):
            validate_schema(df, file_path)
        else:
            logger.info("Skipping schema validation for Dask DataFrame (compute-intensive)")

        summarize_data(df)

        return df
    
    except Exception as e:
        logger.error(f"Failed to read dataset: {e}")
        raise

