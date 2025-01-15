
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import warnings
from statsmodels.tsa.seasonal import seasonal_decompose

warnings.filterwarnings('ignore')

class AgriculturalDataManager:
    def __init__(self):
        """Initialise le gestionnaire de données agricoles"""
        self.monitoring_data = None  # Données de surveillance des cultures
        self.weather_data = None     # Données météorologiques
        self.soil_data = None        # Données sur le sol
        self.yield_history = None    # Historique des rendements
        self.scaler = StandardScaler() # Pour normaliser les données

    def load_data(self):
        """
        Charge l'ensemble des données nécessaires au système
        Effectue les conversions de types et les indexations temporelles
        """
        # Chargement des données de monitoring
        self.monitoring_data = pd.read_csv(r'../../data/monitoring_cultures.csv', 
                                         parse_dates=['date'])
        self.monitoring_data.set_index('date', inplace=True)
        
        # Chargement des données météo
        self.weather_data = pd.read_csv(r'../../data/meteo_detaillee.csv', 
                                      parse_dates=['date'])
        self.weather_data.set_index('date', inplace=True)
        
        # Chargement des données du sol
        self.soil_data = pd.read_csv(r'../../data/sols.csv')
        
        # Chargement de l'historique des rendements
        self.yield_history = pd.read_csv(r'../../data/historique_rendements.csv', 
                                       parse_dates=['date'])
        self.yield_history.set_index('date', inplace=True)
        # Convertir les dates en datetime
        self.monitoring_data['date'] = pd.to_datetime(self.monitoring_data.index, errors='coerce')
        print("Données de monitoring chargées et colonne 'date' convertie.")
        self.weather_data['date'] = pd.to_datetime(self.weather_data.index, errors='coerce')
        self.yield_history['date'] = pd.to_datetime(self.yield_history.index.astype(str), format='%Y', errors='coerce')

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
        """
        Configure les index temporels pour les différentes séries
        de données et vérifie leur cohérence
        """
        # Vérification que tous les DataFrames ont des index temporels
        for df_name, df in [('monitoring', self.monitoring_data),
                          ('weather', self.weather_data),
                          ('yield', self.yield_history)]:
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValueError(f"L'index temporel est manquant pour {df_name}")
        
        # Alignement des fréquences d'échantillonnage
        self.monitoring_data = self.monitoring_data.asfreq('D')
        self.weather_data = self.weather_data.asfreq('D')
        self.yield_history = self.yield_history.asfreq('D')
    
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
    ##########
    
    
    def verify_temporal_consistency(self):
        """
        Vérifie la cohérence des périodes temporelles entre
        les différents jeux de données
        """
        # Vérification des périodes couvertes
        start_dates = []
        end_dates = []
        
        for df in [self.monitoring_data, self.weather_data, self.yield_history]:
            if df is not None:
                start_dates.append(df.index.min())
                end_dates.append(df.index.max())
        
        # Vérification de la cohérence temporelle
        if max(start_dates) > min(end_dates):
           raise ValueError("Les périodes temporelles des données ne se chevauchent pas")
        return True

    def prepare_features(self, data):
        """
           Prépare les caractéristiques pour l'analyse en fusionnant
           les différentes sources de données
        """
        try:
            if not all([self.monitoring_data is not None, self.weather_data is not None, self.soil_data is not None]):
                raise ValueError("Données insuffisantes pour préparer les caractéristiques. "
                            "Veuillez vérifier que monitoring_data, weather_data et soil_data sont chargées.")
        
        # Création d'une copie des données de monitoring comme base
            features = data.copy()

        # Fusion avec les données météo
            features = pd.merge_asof(
            features.sort_index(),
            self.weather_data.sort_index(),
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta('1H')
        )

        # Fusion avec les données de sol
            if 'parcelle_id' not in self.soil_data.columns:
               raise ValueError("La colonne 'parcelle_id' est manquante dans les données de sol.")
        
            features = features.merge(self.soil_data, on='parcelle_id', how='left')

        # Normalisation des caractéristiques numériques
            numeric_columns = features.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) == 0:
               raise ValueError("Aucune colonne numérique trouvée pour la normalisation.")
        
            features[numeric_columns] = self.scaler.fit_transform(features[numeric_columns])

            return features

        except Exception as e:
            raise ValueError(f"Erreur lors de la préparation des caractéristiques : {str(e)}")
        
    ###########
    def _enrich_with_yield_history(self, data):
        """
        Enrichit les données actuelles avec les informations
        historiques des rendements
        """
        # Calcul des statistiques historiques de rendement par parcelle
        historical_stats = self.yield_history.groupby('parcelle_id').agg({
            'rendement': ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        # Fusion avec les données actuelles
        enriched_data = data.merge(
            historical_stats,
            on='parcelle_id',
            how='left'
        )
        
        return enriched_data

    def get_temporal_patterns(self, parcelle_id: int):
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
        # Filtrage des données pour la parcelle spécifique
        parcelle_data = self.monitoring_data[
            self.monitoring_data['parcelle_id'] == parcelle_id
        ].copy()
        
        # Identifier la première colonne numérique pour l'analyse
        numeric_cols = parcelle_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
           raise ValueError("Aucune colonne numérique trouvée pour l'analyse")
    
           target_col = numeric_cols[0]  # Utiliser la première colonne numérique
    
    # Calcul des moyennes mobiles
           parcelle_data['ma_7j'] = parcelle_data[target_col].rolling(window=7).mean()
           parcelle_data['ma_30j'] = parcelle_data[target_col].rolling(window=30).mean()
    
        return (history,trend)

    def calculate_risk_metrics(self, data):
        """
        Calcule les métriques de risque basées sur les conditions
        actuelles et l'historique
        """
        risk_metrics = pd.DataFrame()
        # Identifier la colonne cible pour le calcul des risques
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
           raise ValueError("Aucune colonne numérique trouvée pour le calcul des risques")
    
        target_col = numeric_cols[0]  # Utiliser la première colonne numérique
    
        if 'rendement' in self.yield_history:
            mean_yield = self.yield_history['rendement'].mean()
            std_yield = self.yield_history['rendement'].std()
        # Calcul des écarts par rapport aux moyennes historiques
            risk_metrics['deviation_from_mean'] = (
            data['valeur'] - data['rendement']['mean']
            ) / data['rendement']['std']
        
        # Calcul du score de risque
            risk_metrics['risk_score'] = 1 / (1 + np.exp(-risk_metrics['deviation_from_mean']))
        return risk_metrics
        return features

    def analyze_yield_patterns(self, parcelle_id):
        """
        Réalise une analyse approfondie des patterns de rendement
        """
        # Extraction et préparation des données
        history = self.yield_history[
            self.yield_history['parcelle_id'] == parcelle_id
        ].copy()
        
        # Décomposition temporelle
        decomposition = seasonal_decompose(
            history['rendement'],
            period=12,  # Période annuelle
            extrapolate_trend='freq'
        )
        
        return {
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        }