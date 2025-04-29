from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship

import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle
import io
import json

from DataSetDB import obter_delimitador, getDatasetFeatures
class ModeloPreditivo(db.Model):
    __tablename__ = 'modelo_preditivo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    modelo_serializado = Column(LargeBinary)
    imagem_matriz_confusao = Column(LargeBinary)
    metricas = Column(Text)
    hiper_parametros = Column(Text)
    utilizador_id = Column(Integer, ForeignKey('utilizador.id'))
    dataset_criacao_id = Column(Integer, ForeignKey('dataset.id'))
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    features_utilizadas = Column(JSON)
    tipo_modelo = Column(String(50), default="LinearRegression")
    normalizador_serializado = Column(LargeBinary)

    utilizador = relationship('Utilizador', back_populates='modelos')
    dataset_criacao = relationship('Dataset', back_populates='modelos')
    previsoes = relationship('Previsao', back_populates='modelo')

def getModels(user_id):
    try:
        db_search = ModeloPreditivo.query.all()
        return db_search
    except Exception as e:
        db.session.rollback()  
        print(f"Erro ao encontrar Modelos: {e}")
        return 0
    
def getModelsByID(id):
    try:
        db_search = ModeloPreditivo.query.filter_by(id = id).first() 
        return db_search
    except Exception as e:
        db.session.rollback()  
        print(f"Erro ao encontrar Modelo: {e}")
        return 0
    
def remModel(id):
    try:
        db_search = ModeloPreditivo.query.filter_by(id = id).first() 
        db.session.delete(db_search)
        db.session.commit()
        return 1
    except Exception as e:
        db.session.rollback()  
        print(f"Erro ao remover Modelo: {e}")
        return 0
    
def addModels(modelo):
    try:
        db.session.add(modelo)
        db.session.commit()
        print(f"Modelo {modelo.nome} guardado com sucesso!")
        return 1
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao guardar Modelo: {e}")
        return 0

def getCompatibleModels(ds_id):
    ds_features = getDatasetFeatures(ds_id)
    all_models = ModeloPreditivo.query.all()

    modelos_compativeis = []

    for modelo in all_models:
        if set(modelo.features_utilizadas).issubset(set(ds_features)):
            modelos_compativeis.append(modelo)

    return modelos_compativeis

    
def createModelLinearRegkold(ds_path, nome, threshold, kfold_n, col_rem, user_id, ds_id):

    with open(ds_path, 'rb') as buffer:
        delimitador = obter_delimitador(buffer)

    df = pd.read_csv(ds_path, delimiter = delimitador)

    # Modelos, feature e váriaveis objetivo
    x = df.drop(columns=['Target'] + col_rem)
    y = df['Target'].apply(lambda x: 1 if x == 'Dropout' else 0)

    modelo = LinearRegression()

    #Normalização dos dados 
    scaler = StandardScaler()
    x_scaled = pd.DataFrame(scaler.fit_transform(x), columns=x.columns)

    matriz_confusao_acumulada = np.zeros((2, 2))

    accuracy_list = []
    precision_list = []
    recall_list = []
    f1_list = []

    kf = StratifiedKFold(n_splits= kfold_n, shuffle=True, random_state=42)

    for i_train, i_test in kf.split(x_scaled, y):
        x_train, x_test = x_scaled.iloc[i_train], x_scaled.iloc[i_test]
        y_train, y_test = y.iloc[i_train], y.iloc[i_test]

        #Treino do modelo
        modelo.fit(x_train, y_train)

        #Resultado de valores continuos 
        res_continuos = modelo.predict(x_test) 

        #Converter de valores continuos para Valores Binários
        intervalo_de_admissao = threshold
        res_binario = (res_continuos >= intervalo_de_admissao).astype(int)

        matriz_confusao_acumulada += confusion_matrix(y_test, res_binario)

        #Calculo de Metricas
        accuracy_list.append(accuracy_score(y_test, res_binario))
        precision_list.append(precision_score(y_test, res_binario))
        recall_list.append(recall_score(y_test, res_binario))
        f1_list.append(f1_score(y_test, res_binario))

    # Plotar a matriz de confusão final
    plt.figure(figsize=(6, 4))
    sns.heatmap(matriz_confusao_acumulada.astype(int), annot=True, fmt='d', cmap="Blues", xticklabels=["Graduate (0)", "Dropout (1)"], yticklabels=["Graduate (0)", "Dropout (1)"])
    plt.xlabel("Previsto")
    plt.ylabel("Real")
    plt.title("Matriz de Confusão - Cross Validation")
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    imagem_matriz_confusao_bin = img_buffer.read()
    
    #Features utilizadas
    features_utilizadas = x.columns.tolist()

    #serialização do modelo e normalizador
    modelo_serializado = pickle.dumps(modelo)
    norm_ser = pickle.dumps(scaler)


    metricas_dict = {
        "acuracia": np.mean(accuracy_list),
        "precisao": np.mean(precision_list),
        "recall": np.mean(recall_list),
        "f1_score": np.mean(f1_list)
    }
    hiper_parametros = {
        "tipo_modelo": "LinearRegression",
        "intervalo_admissao": intervalo_de_admissao,
        "normalizacao": "StandardScaler",
        "num_folds": kfold_n,
    }

    metricas_json = json.dumps(metricas_dict)
    hiper_parametros_json = json.dumps(hiper_parametros)

    novo_modelo = ModeloPreditivo(
    nome= nome,
    modelo_serializado=modelo_serializado,
    imagem_matriz_confusao=imagem_matriz_confusao_bin,
    metricas=metricas_json,
    hiper_parametros=hiper_parametros_json,
    tipo_modelo="LinearRegression",
    normalizador_serializado = norm_ser,
    features_utilizadas = features_utilizadas,
    utilizador_id=user_id, 
    dataset_criacao_id=ds_id 
)
    return(novo_modelo)


def createModelLinearRegTrainTestSplit(ds_path, nome, threshold, split_ratio, col_rem, user_id, ds_id):
    with open(ds_path, 'rb') as buffer:
        delimitador = obter_delimitador(buffer)

    df = pd.read_csv(ds_path, delimiter = delimitador)

    # Modelos, feature e váriaveis objetivo
    x = df.drop(columns=['Target'] + col_rem)
    y = df['Target'].apply(lambda x: 1 if x == 'Dropout' else 0)

    modelo = LinearRegression()

    #Normalização dos dados 
    scaler = StandardScaler()
    x_scaled = pd.DataFrame(scaler.fit_transform(x), columns=x.columns)

    matriz_confusao = np.zeros((2, 2))

    x_train, x_test, y_train, y_test = train_test_split(x_scaled, y, test_size=split_ratio, random_state=42)

    modelo.fit(x_train, y_train)

    #Resultado de valores continuos 
    res_continuos = modelo.predict(x_test) 

    #Converter de valores continuos para Valores Binários
    intervalo_de_admissao = threshold
    res_binario = (res_continuos >= intervalo_de_admissao).astype(int)

    matriz_confusao += confusion_matrix(y_test, res_binario)
    accuracy=(accuracy_score(y_test, res_binario))
    precision =(precision_score(y_test, res_binario))
    recall = (recall_score(y_test, res_binario))
    f1=(f1_score(y_test, res_binario))

    # Plotar a matriz de confusão final
    plt.figure(figsize=(6, 4))
    sns.heatmap(matriz_confusao.astype(int), annot=True, fmt='d', cmap="Blues", xticklabels=["Graduate (0)", "Dropout (1)"], yticklabels=["Graduate (0)", "Dropout (1)"])
    plt.xlabel("Previsto")
    plt.ylabel("Real")
    plt.title("Matriz de Confusão - Cross Validation")
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    imagem_matriz_confusao_bin = img_buffer.read()
    
    #Features utilizadas
    features_utilizadas = x.columns.tolist()

    #serialização do modelo e normalizador
    modelo_serializado = pickle.dumps(modelo)
    norm_ser = pickle.dumps(scaler)


    metricas_dict = {
        "acuracia": accuracy,
        "precisao": precision,
        "recall": recall,
        "f1_score": f1
    }
    hiper_parametros = {
        "tipo_modelo": "LinearRegression",
        "intervalo_admissao": intervalo_de_admissao,
        "normalizacao": "StandardScaler",
        "split_ratio": split_ratio,
    }

    metricas_json = json.dumps(metricas_dict)
    hiper_parametros_json = json.dumps(hiper_parametros)

    novo_modelo = ModeloPreditivo(
    nome= nome,
    modelo_serializado=modelo_serializado,
    imagem_matriz_confusao=imagem_matriz_confusao_bin,
    metricas=metricas_json,
    hiper_parametros=hiper_parametros_json,
    tipo_modelo="LinearRegression",
    normalizador_serializado = norm_ser,
    features_utilizadas = features_utilizadas,
    utilizador_id=user_id, 
    dataset_criacao_id=ds_id 
)
    
    return(novo_modelo)


def prever(self, dataset_path):
    with open(dataset_path, "rb") as f:
        file_bytes = f.read()
        buffer = io.BytesIO(file_bytes)
        delimitador = obter_delimitador(buffer)

    df = pd.read_csv(io.BytesIO(file_bytes), delimeter = delimitador)

    x = df[self.features_utilizadas]
    scaler = pickle.loads(self.normalizador_serializado)
    x_scaled = scaler.transform(x)
        
    modelo = pickle.loads(self.modelo_serializado)
    previsoes_continuas = modelo.predict(x_scaled)
    threshold = json.loads(self.hiper_parametros)["intervalo_admissao"]

    return (previsoes_continuas >= threshold).astype(int)
