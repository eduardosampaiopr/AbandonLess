import time
import pandas as pd
import numpy as np
from io import BytesIO

def simular_processamento(df):
    inicio = time.time()

    if df.isnull().values.any():
        df = df.dropna()
    t_dropna = time.time()

    df = pd.get_dummies(df, drop_first=True, dtype=int)
    t_dummies = time.time()

    print(f"Tempo dropna: {t_dropna - inicio:.3f}s")
    print(f"Tempo get_dummies: {t_dummies - t_dropna:.3f}s")
    print(f"Tempo total: {t_dummies - inicio:.3f}s")

if __name__ == "__main__":
    df = pd.read_csv("Flask/testes/dataset_grande.csv", sep=';')
    simular_processamento(df)
