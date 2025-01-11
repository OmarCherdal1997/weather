import pandas as pd

file_path = r"C:\Users\Dell\OneDrive\Desktop\Projet AgiculturalDataManager\data"  # Remplacez par le chemin correct
data = pd.read_csv(file_path)

print(data.head())  # Affiche les 5 premières lignes
print(data.columns)  # Vérifie les colonnes disponibles
