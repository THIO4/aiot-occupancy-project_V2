import pandas as pd
from pymongo import ASCENDING

from db import get_collection

def load_data():
    """Lataa kaikki kävijähavainnot MongoDB:stä Pandas-analyysiä varten."""
    cursor = get_collection().find(
        {},
        {"_id": 0, "timestamp": 1, "device_id": 1, "topic": 1, "occupancy": 1},
    ).sort("timestamp", ASCENDING)
    df = pd.DataFrame(list(cursor))

    if df.empty:
        return pd.DataFrame(columns=["timestamp", "device_id", "topic", "occupancy"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["occupancy"] = pd.to_numeric(df["occupancy"], errors="coerce")
    df = df.dropna(subset=["timestamp", "occupancy"])
    return df

def get_24h_profile(df):
    if df.empty:
        return pd.DataFrame(columns=['hour', 'predicted_occupancy'])
    
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    
    # Lasketaan keskiarvo ja pyöristetään kokonaisluvuksi
    profile = df.groupby('hour')['occupancy'].mean().round(0).astype(int).reset_index()
    profile.rename(columns={'occupancy': 'predicted_occupancy'}, inplace=True)
    
    all_hours = pd.DataFrame({'hour': range(24)})
    profile = pd.merge(all_hours, profile, on='hour', how='left').fillna(0)
    return profile

def get_weekly_heatmap_data(df):
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['day_name'] = df['timestamp'].dt.day_name()
    
    # Käytetään max() keskiarvon sijaan, jotta piikit näkyvät paremmin.
    # Pyöristetään ja nimetään sarake valmiiksi.
    heatmap_data = df.groupby(['day_name', 'hour'])['occupancy'].max().round(0).astype(int).reset_index()
    heatmap_data.rename(columns={'occupancy': 'predicted_occupancy'}, inplace=True)
    
    suomi_paivat = {
        'Monday': 'Ma', 'Tuesday': 'Ti', 'Wednesday': 'Ke', 
        'Thursday': 'To', 'Friday': 'Pe', 'Saturday': 'La', 'Sunday': 'Su'
    }
    heatmap_data['day_name'] = heatmap_data['day_name'].map(suomi_paivat)
    return heatmap_data
