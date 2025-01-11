# test_data_generator.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_data():
    """Génère des données de test pour le système agricole"""
    
    # Génération des dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='H')
    
    # Données météo
    weather_data = pd.DataFrame({
        'date': dates,
        'temperature': np.random.normal(20, 5, len(dates)),
        'humidity': np.random.normal(70, 10, len(dates)),
        'precipitation': np.random.exponential(1, len(dates)),
        'wind_speed': np.random.normal(10, 3, len(dates))
    })
    
    # Données de monitoring
    parcelles = ['P001', 'P002', 'P003']
    monitoring_records = []
    
    for parcelle in parcelles:
        daily_dates = pd.date_range(start_date, end_date, freq='D')
        base_ndvi = np.random.normal(0.7, 0.1, len(daily_dates))
        base_lai = np.random.normal(3, 0.5, len(daily_dates))
        
        monitoring_records.extend([{
            'date': date,
            'parcelle_id': parcelle,
            'NDVI': ndvi + np.random.normal(0, 0.05),
            'LAI': lai + np.random.normal(0, 0.2),
            'biomasse': np.random.normal(500, 50)
        } for date, ndvi, lai in zip(daily_dates, base_ndvi, base_lai)])
    
    monitoring_data = pd.DataFrame(monitoring_records)
    
    # Données des sols
    soil_data = pd.DataFrame({
        'parcelle_id': parcelles,
        'type_sol': ['argileux', 'limoneux', 'sableux'],
        'ph': np.random.normal(6.5, 0.5, len(parcelles)),
        'matiere_organique': np.random.normal(3, 0.5, len(parcelles))
    })
    
    # Historique des rendements
    years = range(2020, 2025)
    yield_records = []
    
    for parcelle in parcelles:
        base_yield = np.random.normal(8, 1)
        for year in years:
            yield_records.append({
                'date': datetime(year, 12, 31),
                'parcelle_id': parcelle,
                'rendement': base_yield + np.random.normal(0, 0.5),
                'culture': np.random.choice(['blé', 'maïs', 'colza'])
            })
    
    yield_history = pd.DataFrame(yield_records)
    
    # Sauvegarde des données
    weather_data.to_csv('data/meteo_detaillee.csv', index=False)
    monitoring_data.to_csv('data/monitoring_cultures.csv', index=False)
    soil_data.to_csv('data/sols.csv', index=False)
    yield_history.to_csv('data/historique_rendements.csv', index=False)

if __name__ == "__main__":
    generate_test_data()