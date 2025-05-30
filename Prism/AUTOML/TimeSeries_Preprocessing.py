import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import warnings
import plotly.graph_objs as go


def parse_datetime(df):
    col = input("Enter the column name containing date/time: ")
    try:
        # First attempt: use infer and allow dayfirst for flexibility
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='raise')
        df.set_index(col, inplace=True)
        print(f"DateTime parsing successful with dayfirst=True. Column '{col}' set as index.")
    except Exception as e1:
        print(f"Initial parsing failed: {e1}")
        try:
            # Fallback to mixed format parsing
            df[col] = pd.to_datetime(df[col], format='mixed', dayfirst=True, errors='raise')
            df.set_index(col, inplace=True)
            print(f"DateTime parsing successful with format='mixed'. Column '{col}' set as index.")
        except Exception as e2:
            print(f"Fallback parsing also failed: {e2}")
            print("Please check the date format in your column.")
    return df


def extract_time_features(df):
    """
    Extract time-based features from a DataFrame with a datetime index or column.
    
    Args:
        df: Input DataFrame, expected to have a DatetimeIndex or a datetime column.
    
    Returns:
        df: DataFrame with additional time-based features (year, month, day, weekday, hour, is_weekend).
    
    Raises:
        ValueError: If no valid datetime information is found or parsing fails.
    """
    
    df = df.copy()
    
    # Check if the index is already a DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        print("Using existing DatetimeIndex.")
        datetime_index = df.index
    else:
        # Look for a potential datetime column
        datetime_col = None
        for col in df.columns:
            if col.lower() in ['date', 'datetime', 'time', 'ds']:
                datetime_col = col
                break
        
        if datetime_col is None:
            # Try to infer a datetime column based on data type or content
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_col = col
                    break
                # Sample a few values to check if they can be parsed as datetime
                try:
                    if isinstance(df[col].iloc[0], str):
                        pd.to_datetime(df[col].iloc[0], format='mixed', dayfirst=True)
                        datetime_col = col
                        break
                except (ValueError, TypeError):
                    continue
        
        if datetime_col is None:
            raise ValueError(
                "No DatetimeIndex or valid datetime column found. "
                "Please provide a datetime column (e.g., 'date', 'datetime') or set a DatetimeIndex."
            )
        
        # Parse the datetime column
        try:
            print(f"Parsing datetime column '{datetime_col}'...")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df[datetime_col] = pd.to_datetime(
                    df[datetime_col], format='mixed', dayfirst=True, errors='coerce'
                )
            
            # Check for parsing failures
            if df[datetime_col].isna().any():
                na_count = df[datetime_col].isna().sum()
                print(f"Warning: {na_count} rows failed datetime parsing and will be filled with the earliest valid date.")
                # Fill NaT with the earliest valid date or drop rows
                valid_dates = df[datetime_col].dropna()
                if not valid_dates.empty:
                    df[datetime_col] = df[datetime_col].fillna(valid_dates.min())
                else:
                    raise ValueError("All datetime values are invalid. Cannot proceed.")
            
            # Set the datetime column as index
            df = df.set_index(datetime_col)
            datetime_index = df.index
            print(f"Set '{datetime_col}' as DatetimeIndex.")
        
        except Exception as e:
            raise ValueError(
                f"Failed to parse datetime column '{datetime_col}'. "
                f"Error: {str(e)}. Try ensuring consistent datetime format or use format='mixed' with dayfirst=True."
            )
    
    try:
        df['year'] = datetime_index.year
        df['month'] = datetime_index.month
        df['day'] = datetime_index.day
        df['weekday'] = datetime_index.weekday
        df['hour'] = datetime_index.hour if hasattr(datetime_index, 'hour') else 0
        df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
        print("Time-based features extracted: year, month, day, weekday, hour, is_weekend.")
    except Exception as e:
        raise ValueError(f"Error extracting time features: {str(e)}")
    
    return df


def resample_data(df, datetime_col=None, freq=None, method=None):
    """
    Resample time series data to a specified frequency and aggregate using a chosen method.
    
    Args:
        df: Input DataFrame, expected to have a DatetimeIndex or a datetime column.
        datetime_col: Optional; name of the datetime column to use if not auto-detected.
        freq: Optional; resampling frequency (e.g., 'D', 'W', 'M'). If None, user is prompted.
        method: Optional; aggregation method (e.g., 'mean', 'sum'). If None, user is prompted.
    
    Returns:
        df: Resampled DataFrame with aggregated values, or original DataFrame if resampling is skipped.
    
    Raises:
        ValueError: If resampling fails due to invalid inputs or missing datetime information.
    """
    df = df.copy()  # Avoid modifying the original DataFrame
    
    # Valid frequencies and methods
    valid_freqs = ['D', 'W', 'M', 'H', 'Q', 'Y', 'T', 'S']
    valid_methods = ['mean', 'sum', 'min', 'max', 'median', 'std']
    
    # Automatically detect datetime column if not provided
    if not isinstance(df.index, pd.DatetimeIndex) and datetime_col is None:
        for col in df.columns:
            # Check for common datetime column names
            if col.lower() in ['date', 'datetime', 'time', 'ds']:
                datetime_col = col
                break
            # Try to infer datetime column by sampling values
            try:
                sample = df[col].dropna().iloc[:5]  # Sample up to 5 non-null values
                if sample.empty:
                    continue
                # Check if column can be parsed as datetime
                pd.to_datetime(sample, format='mixed', dayfirst=True, errors='raise')
                datetime_col = col
                break
            except (ValueError, TypeError):
                continue
        
        if datetime_col is None:
            print("Warning: No DatetimeIndex or valid datetime column found. Skipping resampling.")
            return df  # Return original DataFrame if no datetime info is available
    
    # Parse datetime column if provided or detected
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            print(f"Attempting to parse datetime column '{datetime_col}'...")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df[datetime_col] = pd.to_datetime(
                    df[datetime_col], format='mixed', dayfirst=True, errors='coerce'
                )
            
            # Handle invalid datetime values
            if df[datetime_col].isna().any():
                na_count = df[datetime_col].isna().sum()
                print(f"Warning: {na_count} rows failed datetime parsing and will be dropped.")
                df = df.dropna(subset=[datetime_col])
                if df.empty:
                    print("Error: All rows dropped due to invalid datetime values. Skipping resampling.")
                    return df  # Return empty DataFrame or original if preferred
            
            # Set as index
            df = df.set_index(datetime_col)
            print(f"Set '{datetime_col}' as DatetimeIndex.")
        except Exception as e:
            print(f"Error parsing datetime column '{datetime_col}': {str(e)}. Skipping resampling.")
            return df
    
    # Verify DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        print("Error: Failed to create a valid DatetimeIndex. Skipping resampling.")
        return df
    
    # Get resampling parameters
    if freq is None:
        freq = input(
            "Enter resampling frequency (e.g., 'D' for daily, 'W' for weekly, 'M' for monthly, or 'skip' to skip): "
        ).strip()
    if freq.lower() == 'skip':
        print("Resampling skipped by user.")
        return df
    if freq not in valid_freqs:
        print(f"Invalid frequency '{freq}'. Choose from {valid_freqs}. Skipping resampling.")
        return df
    
    if method is None:
        method = input("Aggregation method (mean/sum/min/max/median/std, or 'skip' to skip): ").strip().lower()
    if method.lower() == 'skip':
        print("Resampling skipped by user.")
        return df
    if method not in valid_methods:
        print(f"Invalid method '{method}'. Choose from {valid_methods}. Skipping resampling.")
        return df
    
    # Restrict to numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if not numeric_cols.any():
        print("Error: No numeric columns found for aggregation. Skipping resampling.")
        return df
    df = df[numeric_cols].fillna(df[numeric_cols].mean())  # Fill NaN with column mean
    
    # Perform resampling
    try:
        df = df.resample(freq).agg(method)
        print(f"Data resampled using {method} at {freq} frequency.")
    except Exception as e:
        print(f"Error in resampling: {str(e)}. Returning original DataFrame.")
        return df
    
    return df



def create_lag_rolling(df):
    col = input("Enter column for lag/rolling: ")
    try:
        lag = int(input("Enter lag value: "))
        roll = int(input("Enter rolling window size: "))
        df[f'{col}_lag{lag}'] = df[col].shift(lag)
        df[f'{col}_roll_mean{roll}'] = df[col].rolling(roll).mean()
        df[f'{col}_roll_std{roll}'] = df[col].rolling(roll).std()
        print("Lag and rolling features created.")
    except Exception as e:
        print(f"Error in lag/rolling: {e}")
    return df


def seasonal_decompose_ts(df):
    col = input("Enter column to decompose: ")
    model = input("Decomposition model (additive/multiplicative): ")
    freq = int(input("Enter frequency (e.g., 12 for monthly, 365 for daily): "))

    try:
        result = seasonal_decompose(df[col], model=model, period=freq)
        df[f'{col}_trend'] = result.trend
        df[f'{col}_seasonal'] = result.seasonal
        df[f'{col}_resid'] = result.resid

        # Create interactive subplots
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index, y=result.observed,
            name='Observed',
            mode='lines'
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=result.trend,
            name='Trend',
            mode='lines'
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=result.seasonal,
            name='Seasonal',
            mode='lines'
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=result.resid,
            name='Residual',
            mode='lines'
        ))

        fig.update_layout(
            title=f'Seasonal Decomposition of {col} ({model.capitalize()} model)',
            xaxis_title='Date',
            yaxis_title='Value',
            height=800
        )
        fig.show()

        print(" Seasonal decomposition completed and plotted interactively.")
    except Exception as e:
        print(f" Error in decomposition: {e}")

    return df


def stationarity_test(df):
    col = input("Enter column for stationarity check: ")
    try:
        result = adfuller(df[col].dropna())
        print(f"ADF Statistic: {result[0]}")
        print(f"p-value: {result[1]}")
        if result[1] < 0.05:
            print("The series is likely stationary.")
        else:
            print("The series is likely non-stationary.")
    except Exception as e:
        print(f"Error in ADF test: {e}")
    return df

def time_series_preprocessing_pipeline(df):
    while True:
        print("\nTime-Series Preprocessing Menu:")
        print("1. Parse DateTime and set index")
        print("2. Extract time-based features")
        print("3. Resample data")
        print("4. Create lag/rolling features")
        print("5. Seasonal decomposition")
        print("6. Check stationarity (ADF test)")

        choice = input("Select an option (1-6): ")

        if choice == '1':
            df = parse_datetime(df)
        elif choice == '2':
            df = extract_time_features(df)
        elif choice == '3':
            df = resample_data(df)
        elif choice == '4':
            df = create_lag_rolling(df)
        elif choice == '5':
            df = seasonal_decompose_ts(df)
        elif choice == '6':
            df = stationarity_test(df)
        else:
            print("Invalid choice.")

        cont = input("\nDo you want to perform another time-series transformation? (yes/no): ").strip().lower()
        if cont != 'yes':
            break

    return df

