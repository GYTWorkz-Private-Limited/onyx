import pandas as pd
import numpy as np
from pycaret.anomaly import *
from pyod.models.iforest import IForest
from pyod.models.knn import KNN
from pyod.models.lof import LOF
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

def detect_anomalies_pycaret_pyod(df):
    print("\nColumns in your data:")
    print(df.columns.tolist())

    # Ensure input is a Pandas DataFrame
    print(f"Input data type: {type(df)}")
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
        print("Converted input to Pandas DataFrame")

    # Check for datetime column
    is_time_series = False
    datetime_col = None
    if 'date' in df.columns or 'Date' in df.columns:
        datetime_col = 'date' if 'date' in df.columns else 'Date'
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        is_time_series = True
    elif all(col in df.columns for col in ['year', 'month', 'day']):
        if 'hour' in df.columns:
            df['ds'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
        else:
            df['ds'] = pd.to_datetime(df[['year', 'month', 'day']])
        datetime_col = 'ds'
        is_time_series = True
    elif isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index().rename(columns={'index': 'ds'})
        datetime_col = 'ds'
        is_time_series = True

    # Select numeric columns for anomaly detection
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    cols_to_exclude = ['YearMonth']  # Add columns to exclude if needed
    numeric_cols = [col for col in numeric_cols if col not in cols_to_exclude]
    
    if not numeric_cols:
        raise ValueError("No numeric columns available for anomaly detection.")

    target_col = input(f"\nEnter the target column for anomaly detection (available: {numeric_cols}): ")

    # Validate target column
    if target_col not in df.columns or target_col not in numeric_cols:
        raise ValueError(f"Target column '{target_col}' not found in numeric columns.")

    # Handle missing values
    print(f"Missing values before preprocessing: {df.isna().sum()}")
    df = df.fillna(df[numeric_cols].mean())

    # Aggregate duplicates by mean for time series data
    if is_time_series:
        analysis_cols = numeric_cols + [datetime_col]
        print(f"Dataset size before preprocessing: {len(df)}")
        df = df.groupby(datetime_col, as_index=False).mean(numeric_only=True)
        print(f"Dataset size after aggregation: {len(df)}")
        if is_time_series:
            df = df.set_index(datetime_col)
    else:
        print(f"Dataset size: {len(df)} rows")

    # Check data size
    if len(df) < 10:
        raise ValueError(f"Dataset has {len(df)} rows, but at least 10 are required for anomaly detection.")

    # Initialize PyCaret anomaly detection environment
    print("\nSetting up PyCaret anomaly detection...")
    anomaly_df = df[numeric_cols].copy()
    try:
        setup(anomaly_df, session_id=123, verbose=False, normalize=True, numeric_imputation='mean')
    except Exception as e:
        print(f"Error in PyCaret setup: {str(e)}")
        print("Possible dependency issue. Try: pip install pycaret==3.3.0")
        raise

    # Define PyCaret models
    pycaret_models = ['iforest', 'knn', 'lof', 'svm', 'pca', 'mcd']
    results = {}
    anomaly_labels_all = []

    # Train and evaluate PyCaret models
    for model_name in pycaret_models:
        try:
            print(f"\nTraining PyCaret model: {model_name}...")
            model = create_model(model_name)
            predictions = assign_model(model)
            
            # Extract anomaly labels and scores
            anomaly_labels = predictions['Anomaly']
            anomaly_scores = predictions['Anomaly_Score']
            
            # Add model-specific columns to DataFrame
            df[f'{model_name}_Anomaly_Score'] = anomaly_scores
            df[f'{model_name}_Anomaly'] = anomaly_labels
            
            # Store results
            results[model_name] = {
                'anomalies': anomaly_labels.sum(),
                'scores': anomaly_scores,
                'labels': anomaly_labels
            }
            anomaly_labels_all.append(anomaly_labels)
            
            print(f"Number of anomalies detected by {model_name}: {anomaly_labels.sum()}")
            
        except Exception as e:
            print(f"Error evaluating PyCaret model {model_name}: {str(e)}")

    # Define PyOD models
    pyod_models = {
        'iforest': IForest(contamination=0.1, random_state=123),
        'knn': KNN(contamination=0.1),
        'lof': LOF(contamination=0.1)
    }

    # Train and evaluate PyOD models
    scaler = StandardScaler()
    X = scaler.fit_transform(df[[target_col]])
    
    for model_name, model in pyod_models.items():
        try:
            print(f"\nTraining PyOD model: {model_name}...")
            model.fit(X)
            anomaly_labels = model.predict(X)
            anomaly_scores = model.decision_scores_
            
            # Add model-specific columns to DataFrame
            df[f'pyod_{model_name}_Anomaly_Score'] = anomaly_scores
            df[f'pyod_{model_name}_Anomaly'] = anomaly_labels
            
            # Store results
            results[f"pyod_{model_name}"] = {
                'anomalies': anomaly_labels.sum(),
                'scores': anomaly_scores,
                'labels': anomaly_labels
            }
            anomaly_labels_all.append(anomaly_labels)
            
            print(f"Number of anomalies detected by pyod_{model_name}: {anomaly_labels.sum()}")
            
        except Exception as e:
            print(f"Error evaluating PyOD model {model_name}: {str(e)}")

    # Determine final anomalies (majority voting: at least half of models agree)
    if anomaly_labels_all:
        anomaly_labels_df = pd.DataFrame(anomaly_labels_all).T
        majority_threshold = len(anomaly_labels_all) // 2
        df['Final_Anomaly'] = (anomaly_labels_df.sum(axis=1) >= majority_threshold).astype(int)
        print(f"\nNumber of final anomalies (majority voting): {df['Final_Anomaly'].sum()}")

    # Create summary table
    summary_data = {
        'Model': [],
        'Number of Anomalies': []
    }
    for model_name, result in results.items():
        summary_data['Model'].append(model_name)
        summary_data['Number of Anomalies'].append(result['anomalies'])
    
    summary_df = pd.DataFrame(summary_data)
    print("\nSummary of Anomaly Detection Results:")
    print(summary_df)

    # Save results
    print("\nSaving results...")
    df.to_csv('data_with_anomalies.csv', index=True)

    # Generate visualizations
    print("\nGenerating visualizations...")

    # 1. Distribution of anomaly scores (Isolation Forest)
    plt.figure(figsize=(10, 6))
    sns.histplot(df['iforest_Anomaly_Score'], kde=True, color='blue')
    plt.title('Distribution of Anomaly Scores (Isolation Forest)')
    plt.savefig('anomaly_score_distribution.png')
    plt.close()

    # 2. Interactive 3D Scatter Plot for Final Anomalies
    if len(numeric_cols) >= 2:  # Need at least 2 numeric columns for 3D plot
        plot_df = df.reset_index() if is_time_series else df
        # Collect hover data (all columns except anomaly scores, plus model anomaly labels)
        hover_cols = [col for col in plot_df.columns if not col.endswith('_Anomaly_Score')]
        # Ensure model anomaly labels are included
        model_anomaly_cols = [col for col in plot_df.columns if col.endswith('_Anomaly')]
        hover_cols = list(set(hover_cols + model_anomaly_cols))
        # Remove target column if it's already used in axes
        hover_cols = [col for col in hover_cols if col not in [numeric_cols[0], numeric_cols[1], target_col]]
        
        fig = px.scatter_3d(
            plot_df,
            x=numeric_cols[0],
            y=numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0],
            z=target_col,
            color='Final_Anomaly',
            color_continuous_scale=['blue', 'red'],
            title='3D Scatter Plot of Final Anomalies (Majority Voting)',
            labels={'Final_Anomaly': 'Final Anomaly'},
            hover_data=hover_cols
        )
        fig.update_traces(marker=dict(size=5))
        fig.write_html('3d_final_anomaly_plot.html')
        print("\nInteractive 3D scatter plot saved as '3d_final_anomaly_plot.html'.")
    else:
        print("\nNot enough numeric columns for 3D scatter plot.")

    # 3. Anomalies by categorical column (e.g., store, customer) if available
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_cols:
        cat_col = categorical_cols[0]  # Use the first categorical column
        anomaly_by_cat = df[df['Final_Anomaly'] == True].groupby(cat_col).size().reset_index()
        anomaly_by_cat.columns = [cat_col, 'Anomaly_Count']
        anomaly_by_cat = anomaly_by_cat.sort_values('Anomaly_Count', ascending=False)
        
        if not anomaly_by_cat.empty:
            plt.figure(figsize=(14, 8))
            sns.barplot(data=anomaly_by_cat.head(10), x=cat_col, y='Anomaly_Count', palette='viridis')
            plt.title(f'Top 10 {cat_col}s by Final Anomaly Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('top_categories_by_anomalies.png')
            plt.close()
            print("\nCategorical anomaly plot saved as 'top_categories_by_anomalies.png'.")
        else:
            print(f"\nNo final anomalies found for {cat_col}. No categorical plot generated.")
    else:
        print("\nNo categorical columns found. Skipping categorical anomaly plot.")

    # Print summary of anomalies
    print("\nSummary of Anomalies:")
    print(f"Total transactions: {len(df)}")
    print(f"Final anomalies (majority voting): {df['Final_Anomaly'].sum()} ({df['Final_Anomaly'].mean()*100:.2f}%)")

    # Display top final anomalies
    print("\nTop 10 Final Anomalies by Isolation Forest Score:")
    display_cols = [target_col, 'iforest_Anomaly_Score', 'Final_Anomaly']
    if categorical_cols:
        display_cols.insert(0, categorical_cols[0])
    model_anomaly_cols = [col for col in df.columns if col.endswith('_Anomaly')]
    display_cols.extend([col for col in model_anomaly_cols if col != 'Final_Anomaly'])
    if is_time_series and datetime_col:
        temp_df = df.reset_index()
        if datetime_col not in display_cols:
            display_cols.insert(0, datetime_col)
    else:
        temp_df = df
        if datetime_col in temp_df.columns and datetime_col not in display_cols:
            display_cols.insert(0, datetime_col)
    top_anomalies = temp_df[temp_df['Final_Anomaly'] == True][display_cols].sort_values('iforest_Anomaly_Score', ascending=False).head(10)
    print(top_anomalies)

    print("\nAnalysis complete! Results saved to 'data_with_anomalies.csv'")
    print("Visualizations saved as PNG and HTML files.")

    return results, summary_df
