import pandas as pd
import numpy as np

def gerar_dataset_grande(caminho, linhas=100_000, colunas_cat=10, colunas_num=5):
    df = pd.DataFrame({
        f"cat_{i}": np.random.choice(["A", "B", "C"], size=linhas) for i in range(colunas_cat)
    })
    for i in range(colunas_num):
        df[f"num_{i}"] = np.random.rand(linhas) * 100
    df["Target"] = np.random.choice([0, 1], size=linhas)
    df.to_csv(caminho, index=False, sep=';')


if __name__ == "__main__":

    caminho = "Flask/testes/dataset_grande.csv"
    gerar_dataset_grande(caminho)