import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle
import io
import json

from Flask.ModeloDB import *

df = pd.read_csv("EDA/datasetRAW.csv", sep = ",")

df = df[df['Target'] != 'Enrolled']

x = df.drop(columns=['Target', 'Nacionality'])
y = df['Target'].apply(lambda x: 1 if x == 'Dropout' else 0)

x.shape, y.shape

#Modelo
modelo = LinearRegression()

#Normalização dos dados para que o algoritmo não de mais importância a valores como idade = 70 em vez de Creaditos aprovados = 18
scaler = StandardScaler()
x_scaled = pd.DataFrame(scaler.fit_transform(x), columns=x.columns)

matriz_confusao_acumulada = np.zeros((2, 2))

# Inicializar StratifiedKFold
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

#Listas para registar os resultados para depois serem feitas as médias
accuracy_list = []
precision_list = []
recall_list = []
f1_list = []

for i_train, i_test in kf.split(x_scaled, y):
    x_train, x_test = x_scaled.iloc[i_train], x_scaled.iloc[i_test] #iloc permite usar linhas/colunas especificas do data set conforme o index
    y_train, y_test = y.iloc[i_train], y.iloc[i_test]

    #Treino do modelo
    modelo.fit(x_train, y_train)

    #Resultado de valores continuos uma vez que estamos a usar regressão linear
    res_continuos = modelo.predict(x_test) #Retorna apenas os resultados da previsão

    #Converter de valores continuos para Valores Binários, problema de regressão para problema de classificação
    intervalo_de_admissao = 0.5
    res_binario = (res_continuos >= intervalo_de_admissao).astype(int)

    matriz_confusao_acumulada += confusion_matrix(y_test, res_binario)

    #Calculo de Metricas
    accuracy_list.append(accuracy_score(y_test, res_binario))
    precision_list.append(precision_score(y_test, res_binario))
    recall_list.append(recall_score(y_test, res_binario))
    f1_list.append(f1_score(y_test, res_binario))

print(f"Acurácia média: {np.mean(accuracy_list):.4f}")
print(f"Precisão média: {np.mean(precision_list):.4f}")
print(f"Recall médio: {np.mean(recall_list):.4f}")
print(f"F1-score médio: {np.mean(f1_list):.4f}")

matriz_confusao_acumulada = matriz_confusao_acumulada.astype(int)
# Plotar a matriz de confusão final
plt.figure(figsize=(6, 4))
sns.heatmap(matriz_confusao_acumulada, annot=True, fmt='d', cmap="Blues", xticklabels=["Graduate (0)", "Dropout (1)"], yticklabels=["Graduate (0)", "Dropout (1)"])
plt.xlabel("Previsto")
plt.ylabel("Real")
plt.title("Matriz de Confusão - Cross Validation")
img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.seek(0)
imagem_matriz_confusao_bin = img_buffer.read()
plt.show()

#serialização do modelo
modelo_serializado = pickle.dumps(modelo)

metricas_dict = {
    "acuracia_media": np.mean(accuracy_list),
    "precisao_media": np.mean(precision_list),
    "recall_medio": np.mean(recall_list),
    "f1_score_medio": np.mean(f1_list)
}
hiper_parametros = {
    "tipo_modelo": "LinearRegression",
    "intervalo_admissao": intervalo_de_admissao,
    "normalizacao": "StandardScaler",
    "n_splits_cv": 5
}

metricas_json = json.dumps(metricas_dict)
hiper_parametros_json = json.dumps(hiper_parametros)


from PIL import Image

# Ver a imagem diretamente a partir do buffer
img_buffer.seek(0)  # garante que começa do início
imagem = Image.open(img_buffer)
imagem.show()

novo_modelo = ModeloPreditivo(
    nome="Modelo Linear Regressão - Dropout",
    modelo_serializado=modelo_serializado,
    imagem_matriz_confusao=imagem_matriz_confusao_bin,
    metricas=metricas_json,
    hiper_parametros=hiper_parametros_json,
    utilizador_id=1,  # substitui com o ID correto
    dataset_criacao_id=1  # substitui com o ID correto
)

db.session.add(novo_modelo)
db.session.commit()