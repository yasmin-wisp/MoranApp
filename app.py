import streamlit as st
import datetime
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

# Define file path and data structure
DATA_FILE = 'symptom_data.csv'
data_entry_structure = {
    'Date': 'datetime64[ns]',
    'Cramps': 'bool',
    'Bloating': 'bool',
    'Mood Swings': 'bool',
    'Fatigue': 'bool',
    'Headaches': 'bool',
    'Back Pain': 'bool',
    'Food Cravings': 'bool',
    'Acne': 'bool'
}
SYMPTOMS = list(data_entry_structure.keys())[1:]


# Define data loading and saving functions
def load_symptom_data(file_path, structure):
    """
    Loads symptom data from a CSV file into a pandas DataFrame.
    """
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, parse_dates=['Date'])
            for col, dtype in structure.items():
                if col not in df.columns:
                    df[col] = pd.NA
                df[col] = df[col].astype(dtype)
            print(f"Symptom data successfully loaded from {file_path}")
        else:
            print(f"No data file found at {file_path}. Returning empty DataFrame.")
            df = pd.DataFrame(columns=structure.keys()).astype(structure)

    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        df = pd.DataFrame(columns=structure.keys()).astype(structure)

    return df

def save_symptom_data(df, file_path):
    """
    Saves the symptom data from a pandas DataFrame to a CSV file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)
        print(f"Symptom data successfully saved to {file_path}")
    except IOError as e:
        print(f"Error saving data to {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving data: {e}")

# Define monthly summary generation function
def generate_monthly_summary(df):
    """
    Generates a monthly summary of symptom prevalence from a daily symptom DataFrame.
    """
    if df.empty:
        print("Input DataFrame is empty. Cannot generate monthly summary.")
        summary_cols = ['Year', 'Month'] + [col for col in df.columns if col != 'Date']
        return pd.DataFrame(columns=summary_cols)

    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    symptom_cols = [col for col in df.columns if col not in ['Date', 'Year', 'Month']]
    monthly_summary = df.groupby(['Year', 'Month'])[symptom_cols].mean() * 100

    monthly_summary = monthly_summary.reset_index()
    monthly_summary = monthly_summary.sort_values(by=['Year', 'Month']).reset_index(drop=True)

    print("Monthly symptom summary generated.")
    return monthly_summary

# Define plotting function
def plot_monthly_summary(monthly_summary_df):
    """
    Generates line plots to visualize symptom trends over months.
    """
    if monthly_summary_df.empty:
        print("No data available in the monthly summary to plot.")
        return

    monthly_summary_df['YearMonth'] = monthly_summary_df['Year'].astype(int).astype(str) + '-' + monthly_summary_df['Month'].astype(int).apply(lambda x: f'{x:02d}')

    symptom_cols = [col for col in monthly_summary_df.columns if col not in ['Year', 'Month', 'YearMonth']]

    if not symptom_cols:
        print("No symptom columns found in the monthly summary DataFrame to plot.")
        return

    num_symptoms = len(symptom_cols)
    fig, axes = plt.subplots(nrows=num_symptoms, ncols=1, figsize=(10, 4 * num_symptoms), sharex=True)

    if num_symptoms == 1:
        axes = [axes]

    for i, symptom in enumerate(symptom_cols):
        axes[i].plot(monthly_summary_df['YearMonth'], monthly_summary_df[symptom], marker='o')
        axes[i].set_title(f'{symptom} Prevalence Over Time')
        axes[i].set_ylabel('Prevalence (%)')
        axes[i].grid(True)

    axes[-1].set_xlabel('Month')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


# Load existing data at the beginning
all_symptom_data_df = load_symptom_data(DATA_FILE, data_entry_structure)


st.title("Period Tracker Application")
st.write("Welcome to the Period Tracker Application! Use this app to record your daily PMS symptoms, view monthly summaries, and visualize your symptom trends.")

st.header("Record Daily Symptoms")

selected_date = st.date_input("Select Date", datetime.date.today())

daily_symptoms_input = {}
st.write("Please check the symptoms you experienced:")
for symptom in SYMPTOMS:
    daily_symptoms_input[symptom] = st.checkbox(symptom)

submit_button = st.button("Record Symptoms")

if submit_button:
    new_entry = {'Date': pd.to_datetime(selected_date)}
    new_entry.update(daily_symptoms_input)
    new_entry_df = pd.DataFrame([new_entry])

    for col, dtype in data_entry_structure.items():
        if col not in new_entry_df.columns:
            new_entry_df[col] = pd.NA
        try:
            new_entry_df[col] = new_entry_df[col].astype(dtype)
        except Exception as e:
            st.warning(f"Warning: Could not convert column '{col}' to dtype '{dtype}': {e}")
            pass

    all_symptom_data_df = pd.concat([all_symptom_data_df, new_entry_df], ignore_index=True)
    all_symptom_data_df = all_symptom_data_df.drop_duplicates(subset=['Date'], keep='last')
    all_symptom_data_df = all_symptom_data_df.sort_values(by='Date').reset_index(drop=True)

    save_symptom_data(all_symptom_data_df, DATA_FILE)
    st.success(f"Symptoms recorded for {selected_date.strftime('%Y-%m-%d')}!")


# Add header for monthly summary section
st.header("Monthly Summary and Trends")

# Add button to trigger the summary and plots
view_summary_button = st.button("View Monthly Summary and Plots")

# Inside an if block that checks if the button was clicked
if view_summary_button:
    # Load the latest data before generating the summary
    all_symptom_data_df = load_symptom_data(DATA_FILE, data_entry_structure)

    # Call the generate_monthly_summary function
    monthly_summary_df = generate_monthly_summary(all_symptom_data_df)

    # Check if the returned monthly summary DataFrame is not empty
    if not monthly_summary_df.empty:
        # Display the monthly summary DataFrame
        st.subheader("Monthly Summary Table")
        st.dataframe(monthly_summary_df)

        # Call the plot_monthly_summary function to display the plots
        st.subheader("Symptom Trends Over Time")
        plot_monthly_summary(monthly_summary_df)
    else:
        # Display a message indicating that no data is available
        st.info("No data available to generate a monthly summary.")
