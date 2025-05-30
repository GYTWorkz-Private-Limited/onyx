from fuzzywuzzy import process
import pandas as pd
import numpy as np
import dask.dataframe as dd
import logging

logger = logging.getLogger(__name__)

def suggest_column_name(user_input, valid_columns):
    match, score = process.extractOne(user_input, valid_columns)
    return match if score > 60 else None

def clean_data(df):
    if isinstance(df, dd.DataFrame):
        logger.info("Computing Dask DataFrame to use Pandas functionality")
        df = df.compute()

    df_cleaned = df.copy()

    while True:
        null_counts = df_cleaned.isnull().sum()
        null_cols = null_counts[null_counts > 0]

        if null_cols.empty:
            print(" No missing values remaining.")
            break

        print("\n⚠️ Columns with Missing Values:")
        print(null_cols)

        print("\nHow would you like to handle missing values?")
        print("1. Remove all rows with missing values")
        print("2. Remove rows with missing values in specific columns")
        print("3. Impute missing values (mean/median/mode/custom)")
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            df_cleaned = df_cleaned.dropna()
            print(" Removed all rows with missing values.")

        elif choice == "2":
            print(f"Columns with missing values: {list(null_cols.index)}")
            user_input_cols = input("Enter column names to drop rows with nulls (comma-separated): ").strip().split(",")
            cols_to_drop = []

            for col in user_input_cols:
                col = col.strip()
                if col not in df_cleaned.columns:
                    suggested = suggest_column_name(col, df_cleaned.columns)
                    if suggested:
                        print(f" Column '{col}' not found. Using suggested column: '{suggested}'")
                        cols_to_drop.append(suggested)
                    else:
                        print(f" Column '{col}' not found. Available columns: {list(df_cleaned.columns)}")
                else:
                    cols_to_drop.append(col)

            df_cleaned = df_cleaned.dropna(subset=cols_to_drop)
            print(f" Dropped rows with nulls in columns: {cols_to_drop}")

        elif choice == "3":
            print("Choose imputation strategy:")
            print("  1. Mean")
            print("  2. Median")
            print("  3. Mode")
            print("  4. Custom Value")
            impute_choice = input("Enter your choice (1/2/3/4): ").strip()

            cols_input = input("Enter columns to impute (comma-separated or 'all'): ").strip()
            if cols_input.lower() == 'all':
                cols = null_cols.index.tolist()
            else:
                raw_cols = [col.strip() for col in cols_input.split(",")]
                cols = []

                for col in raw_cols:
                    if col not in df_cleaned.columns:
                        suggested = suggest_column_name(col, df_cleaned.columns)
                        if suggested:
                            print(f" Column '{col}' not found. Using suggested column: '{suggested}'")
                            cols.append(suggested)
                        else:
                            print(f" Column '{col}' not found. Available columns: {list(df_cleaned.columns)}")
                    else:
                        cols.append(col)

            for col in cols:
                dtype = df_cleaned[col].dropna().dtype
                try:
                    if impute_choice == "1":
                        if pd.api.types.is_numeric_dtype(dtype):
                            value = df_cleaned[col].mean()
                        else:
                            raise TypeError("Mean imputation only works for numeric columns.")
                    elif impute_choice == "2":
                        if pd.api.types.is_numeric_dtype(dtype):
                            value = df_cleaned[col].median()
                        else:
                            raise TypeError("Median imputation only works for numeric columns.")
                    elif impute_choice == "3":
                        value = df_cleaned[col].mode()[0]
                    elif impute_choice == "4":
                        while True:
                            user_val = input(f"Enter custom value for column '{col}' (Expected type: {dtype}): ").strip()

                            try:
                                if pd.api.types.is_numeric_dtype(dtype):
                                    value = float(user_val)
                                    if dtype == int:
                                        value = int(value)
                                elif pd.api.types.is_bool_dtype(dtype):
                                    if user_val.lower() in ['true', '1']:
                                        value = True
                                    elif user_val.lower() in ['false', '0']:
                                        value = False
                                    else:
                                        raise ValueError("Not a valid boolean value.")
                                else:
                                    value = str(user_val)

                                print(f" You entered: {user_val} (type: {type(value).__name__}) | Expected: {dtype}")
                                break
                            except Exception:
                                print(f" Type mismatch. Enter a value compatible with {dtype}. Try again.")
                    else:
                        print(" Invalid imputation choice.")
                        continue

                    df_cleaned[col].fillna(value, inplace=True)
                    print(f" Filled nulls in '{col}' with: {value}")

                except Exception as e:
                    print(f" Error processing column '{col}': {e}")
                    continue

        else:
            print(" Invalid choice. Try again.")

        remaining_nulls = df_cleaned.isnull().sum().sum()
        if remaining_nulls > 0:
            print(f"\n⚠️ {remaining_nulls} missing values still remain.")
            again = input("Do you want to clean remaining missing values? (y/n): ").strip().lower()
            if again != 'y':
                break
        else:
            print(" All missing values handled.")
            break

    return df_cleaned
