import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')
class AgriculturalDataManager:
    def __init__(self):
        self.monitoring_data = None
        self.weather_data = None
        self.soil_data = None
        self.yield_history = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')

    def load_data(self):
        # Charger les données de monitoring
        self.monitoring_data = pd.read_csv(r'../../data/monitoring_cultures.csv')
        self.weather_data = pd.read_csv(r'../../data/meteo_detaillee.csv')
        self.soil_data = pd.read_csv(r'../../data/sols.csv')
        self.yield_history = pd.read_csv(r'../../data/historique_rendements.csv')
        
                        # Convertir les dates en datetime
        self.monitoring_data['date'] = pd.to_datetime(self.monitoring_data['date'], errors='coerce')
        self.weather_data['date'] = pd.to_datetime(self.weather_data['date'], errors='coerce')
        self.yield_history['date'] = pd.to_datetime(self.yield_history['date'].astype(str), format='%Y', errors='coerce')


        # Vérifier les valeurs manquantes
        for dataset_name, dataset in [('monitoring_data', self.monitoring_data), 
                                      ('weather_data', self.weather_data)]:
            missing_count = dataset.isnull().sum().sum()
            if missing_count > 0:
                print(f"Attention : {missing_count} valeurs manquantes détectées dans {dataset_name}.")
        # Vérifiez si des valeurs n'ont pas pu être converties
        if self.weather_data['date'].isnull().any():
            print("Attention : Certaines valeurs dans 'date' n'ont pas pu être converties en datetime dans weather_data.")
        if self.monitoring_data['date'].isnull().any():
            print("Attention : Certaines valeurs dans 'date' n'ont pas pu être converties en datetime dans monitoring_data.")

        # Standardiser les unités de température (Kelvin à Celsius)
        if self.weather_data['temperature'].max() > 100:  # Si la température semble être en Kelvin
            self.weather_data['temperature'] = self.weather_data['temperature'] - 273.15
            print("Température convertie de Kelvin à Celsius.")
        # Harmoniser les dates météo (arrondir à la journée)
    
    def _setup_temporal_indices(self):
        """Configure les index temporels"""
        for df in [self.monitoring_data, self.weather_data, self.yield_history]:
            if df is not None and 'date' in df.columns:
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)

    def _clean_data(self):
        """Nettoie les données"""
        if self.monitoring_data is not None:
            self.monitoring_data.dropna(subset=['parcelle_id'], inplace=True)
            numeric_columns = self.monitoring_data.select_dtypes(include=[np.number]).columns
            self.monitoring_data[numeric_columns] = self.imputer.fit_transform(
                self.monitoring_data[numeric_columns]
            )

        if self.weather_data is not None:
            self.weather_data = self.weather_data.resample('H').mean().interpolate()

    def prepare_features(self):
        if not all([self.monitoring_data is not None, self.weather_data is not None]):
            raise ValueError("Données insuffisantes pour préparer les caractéristiques.")

        self.monitoring_data.index = pd.to_datetime(self.monitoring_data.index)
        self.weather_data.index = pd.to_datetime(self.weather_data.index)

        features = pd.merge_asof(
            self.monitoring_data.sort_index(),
            self.weather_data.sort_index(),
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta('1H')
        )
        features = features.merge(self.soil_data, on='parcelle_id', how='left')
        return features
    # TODO : fix
    def get_temporal_patterns (self, parcelle_id : int):
        """
            Analyse les patterns temporels pour une parcelle donnée
        """
        history = "dummy"
        trend = trend = {
                'pente': 1.23,
                'intercept': 5.67,
                'variation_moyenne': 0.44
            }
        return (history,trend)

    def calculate_risk_metrics (self, features):
        """
        Calcule les métriques de risque basées sur les conditions
        actuelles et l \’ historique
        """
        return features
