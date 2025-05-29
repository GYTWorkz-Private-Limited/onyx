import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

def train_forecast_evaluate_prophet(df):
    print("\nColumns in your data:")
    print(df.columns.tolist())

    target_col = input("\nEnter the target column to forecast: ")

    # Handle datetime column creation
    if 'date' in df.columns or 'Date' in df.columns:
        date_col = 'date' if 'date' in df.columns else 'Date'
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.rename(columns={date_col: 'ds'})
    else:
        if all(col in df.columns for col in ['year', 'month', 'day']):
            if 'hour' in df.columns:
                df['ds'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
            else:
                df['ds'] = pd.to_datetime(df[['year', 'month', 'day']])
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={'index': 'ds'})
        else:
            raise ValueError("No suitable datetime info found.")

    df = df.rename(columns={target_col: 'y'})

    # Aggregate duplicates by mean
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    numeric_cols.append('ds')
    df = df[numeric_cols].groupby('ds', as_index=False).mean()

    df = df.sort_values("ds")

    # User-specified split date
    split_date = input("\nEnter the split date (YYYY-MM-DD) to separate training and test: ")
    split_date = pd.to_datetime(split_date)

    train_df = df[df['ds'] < split_date]
    test_df = df[df['ds'] >= split_date]
    fh = len(test_df)

    print(f"\nTraining on data before {split_date.date()}...")
    model = Prophet()
    model.fit(train_df)

    # Forecast for test period only
    print("\nGenerating forecast...")
    future = model.make_future_dataframe(periods=fh, freq=None)
    forecast = model.predict(future)

    forecast_test = forecast[forecast['ds'].isin(test_df['ds'])]

    # Evaluation
    y_true = test_df['y'].values
    y_pred = forecast_test['yhat'].values

    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)

    print("\nError metrics on test set:")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.2f}%")
    print(f"R2 Score: {r2:.4f}")

    # Plot actual vs forecast (full timeline with test period forecast highlighted)
    plt.figure(figsize=(12, 6))
    plt.plot(df['ds'], df['y'], label='Actual (Full)', color='blue', linewidth=1.5)
    plt.plot(forecast_test['ds'], forecast_test['yhat'], label='Forecast (Test)', color='orange', linewidth=2)
    plt.fill_between(forecast_test['ds'], forecast_test['yhat_lower'], forecast_test['yhat_upper'],
                     color='orange', alpha=0.3, label='Uncertainty Interval')

    # Highlight split
    plt.axvline(x=split_date, color='red', linestyle='--', label='Train/Test Split')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('Prophet Forecast vs Actual')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Components
    print("\nPlotting forecast components...")
    model.plot_components(forecast)
    plt.show()

    print("\nForecasted values vs Actual:")
    result_df = forecast_test[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    result_df['actual'] = test_df['y'].values
    print(result_df)

    return model, result_df


