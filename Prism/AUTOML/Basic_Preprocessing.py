import pandas as pd
import numpy as np
from sklearn.preprocessing import (
    MinMaxScaler, StandardScaler, RobustScaler, MaxAbsScaler,
    Normalizer, QuantileTransformer, PowerTransformer, LabelEncoder, OneHotEncoder
)
from difflib import get_close_matches


def suggest_column(col, columns):
    matches = get_close_matches(col, columns, n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_valid_column(prompt, df):
    col = input(prompt)
    if col in df.columns:
        return col
    suggestion = suggest_column(col, df.columns)
    if suggestion:
        print(f"'{col}' not found. Did you mean '{suggestion}'?")
        use_suggestion = input(f"Use '{suggestion}'? (yes/no): ").lower()
        return suggestion if use_suggestion == 'yes' else None
    else:
        print(f"Column '{col}' not found and no similar columns detected.")
        return None


def encode_categorical(df):
    print("\nEncoding Options:\n1. Label Encoding\n2. One-Hot Encoding\n3. Binary/Target Encoding (Mean Encoding)")
    choice = input("Select an encoding method (1-3): ")

    if choice == '1':
        col = get_valid_column("Enter the column name for Label Encoding: ", df)
        if col:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
    elif choice == '2':
        col = get_valid_column("Enter the column name for One-Hot Encoding: ", df)
        if col:
            df = pd.get_dummies(df, columns=[col])
    elif choice == '3':
        col = get_valid_column("Enter the column for Target Encoding: ", df)
        target = get_valid_column("Enter the target column: ", df)
        if col and target:
            df[col] = df[col].map(df.groupby(col)[target].mean())
    else:
        print("Invalid choice.")

    return df


def scale_normalize(df):
    print("\nScaling/Normalization Options:")
    print("1. Min-Max Scaling\n2. Standardization (Z-score)\n3. Robust Scaler\n4. MaxAbs Scaler\n5. Normalizer (L2 norm)\n6. Quantile Transformer (Normal distribution)")

    choice = input("Select a scaler (1-6): ")
    col = get_valid_column("Enter the numeric column to scale: ", df)
    if not col:
        return df

    scaler = {
        '1': MinMaxScaler(),
        '2': StandardScaler(),
        '3': RobustScaler(),
        '4': MaxAbsScaler(),
        '5': Normalizer(),
        '6': QuantileTransformer(output_distribution='normal')
    }.get(choice)

    if scaler:
        df[col] = scaler.fit_transform(df[[col]])
    else:
        print("Invalid choice.")
    return df


def normalize_transform(df):
    print("\nTransform Options:\n1. Log Transform\n2. Box-Cox Transform\n3. Power Transform (Yeo-Johnson)")
    choice = input("Select a transformation (1-3): ")

    col = get_valid_column("Enter the column to transform: ", df)
    if not col:
        return df

    try:
        if choice == '1':
            df[col] = np.log1p(df[col])
        elif choice == '2':
            pt = PowerTransformer(method='box-cox')
            df[col] = pt.fit_transform(df[[col]])
        elif choice == '3':
            pt = PowerTransformer(method='yeo-johnson')
            df[col] = pt.fit_transform(df[[col]])
        else:
            print("Invalid choice.")
    except Exception as e:
        print(f"Error during transformation: {e}")
    return df


def feature_engineering(df):
    print("\nFeature Engineering Options:")
    print("1. Create new feature from operation on two columns")
    print("2. Binning/Discretization")
    print("3. Aggregation")
    print("4. Running Aggregation (rolling window)")

    choice = input("Select an option (1-4): ")

    if choice == '1':
        col1 = get_valid_column("Enter first column: ", df)
        col2 = get_valid_column("Enter second column: ", df)
        operation = input("Enter operation (+, -, *, /): ")
        new_col = input("Enter new column name: ")

        if col1 and col2:
            try:
                if operation == '+':
                    df[new_col] = df[col1] + df[col2]
                elif operation == '-':
                    df[new_col] = df[col1] - df[col2]
                elif operation == '*':
                    df[new_col] = df[col1] * df[col2]
                elif operation == '/':
                    df[new_col] = df[col1] / df[col2]
                else:
                    print("Invalid operation.")
            except Exception as e:
                print(f"Error during operation: {e}")

    elif choice == '2':
        col = get_valid_column("Enter column to bin: ", df)
        if col:
            bins = int(input("Enter number of bins: "))
            labels = [f"bin_{i}" for i in range(bins)]
            df[f"{col}_binned"] = pd.cut(df[col], bins=bins, labels=labels)
            
            
    elif choice == '3':
        group_cols_input = input("Enter column(s) to group by (comma-separated if multiple): ")
        group_cols = [col.strip() for col in group_cols_input.split(",")]
        group_cols = [col for col in group_cols if col in df.columns]

        if not group_cols:
            print("No valid group-by columns provided.")
            return df

        agg_col_input = input("Enter column(s) to aggregate (comma-separated if multiple): ")
        agg_cols = [col.strip() for col in agg_col_input.split(",")]
        agg_cols = [col for col in agg_cols if col in df.columns]

        if not agg_cols:
            print("No valid aggregation columns provided.")
            return df

        agg_func = input("Enter aggregation function (mean, sum, min, max, std): ").strip().lower()
        if agg_func not in ['mean', 'sum', 'min', 'max', 'std']:
            print("Invalid aggregation function.")
            return df

        try:
            # Generate new column names for each agg col
            for agg_col in agg_cols:
                new_col = f"{'_'.join(group_cols)}_{agg_col}_{agg_func}"
                df[new_col] = df.groupby(group_cols)[agg_col].transform(agg_func)
        except Exception as e:
            print(f"Aggregation error: {e}")


    elif choice == '4':
        col = get_valid_column("Enter column for rolling aggregation: ", df)
        if col:
            try:
                window = int(input("Enter window size: "))
                agg_func = input("Enter rolling function (mean, sum, min, max, std): ")
                new_col = input("Enter new column name for rolling result: ")
                df[new_col] = getattr(df[col].rolling(window), agg_func)()
            except Exception as e:
                print(f"Rolling aggregation error: {e}")
    else:
        print("Invalid option.")

    return df


def data_transformation_pipeline(df):
    while True:
        print("\nMain Data Transformation Menu:")
        print("1. Encoding categorical variables")
        print("2. Scaling/Normalization")
        print("3. Normalize skewed data (Log/Box-Cox/Power)")
        print("4. Feature engineering")

        main_choice = input("Select an option (1-4): ")

        if main_choice == '1':
            df = encode_categorical(df)
        elif main_choice == '2':
            df = scale_normalize(df)
        elif main_choice == '3':
            df = normalize_transform(df)
        elif main_choice == '4':
            df = feature_engineering(df)
        else:
            print("Invalid choice.")

        cont = input("\nDo you want to perform another transformation? (yes/no): ").strip().lower()
        if cont != 'yes':
            break

    return df
