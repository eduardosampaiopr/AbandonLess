import time
from flask import Flask
import sys
import os
import tempfile
import json
import pytest
import pandas as pd
from unittest.mock import patch
import pickle

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Main import app 
from DataSetDB import Dataset
from ModeloDB import ModeloPreditivo

# Teste de velocidade de upload de arquivos
def test_upload_performance():
    client = app.test_client()

    with open("Flask/testes/dataset_grande.csv", "rb") as f:
        start = time.time()
        response = client.post("/ConjuntosDeDados/NovoConjunto", data={"file": f}, follow_redirects=True)
        duration = time.time() - start

    assert response.status_code == 200
    assert duration < 3 
    print(f"Tempo de upload: {duration:.2f} segundos")

# Configuração de app para teste
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["id"] = 2
            sess["tipo_utilizador"] = "Data Scientist"
        yield client


@patch('Routes.getDatasetByID')  # ajusta se o import for diferente
def test_model_creation_train_test_split(mock_get_ds, client):
    ds = Dataset(
        nome="updated_dataset_actv.csv",
        caminho="Flask/testes/updated_dataset_actv.csv",
        num_registos=100000,
        utilizador_id=2,
        is_treino=True,
        coluna_identificadora="Numero de aluno"
    )
    mock_get_ds.return_value = ds

     # Define sessão simulada
    with client.session_transaction() as sess:
        sess["user"] = "test_user"
        sess["id"] = 2 
        sess["tipo_utilizador"] = "Data Scientist"

    response = client.post("/Modelacao/NovoModelo/create", data={
        "nome_modelo": "ModeloTesteTrainTest",
        "threshold": "0.5",
        "validacao": "split",
        "split_ratio": "0.8",
        "colunas_remover": ["Nacionality"],
        "dataset_id": "1",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"metricas" in response.data or b"Matriz" in response.data

@patch('Routes.getDatasetByID')
def test_model_creation_kfold(mock_get_ds, client):
    ds = Dataset(
        nome="updated_dataset_actv.csv",
        caminho="Flask/testes/updated_dataset_actv.csv",
        num_registos=100000,
        utilizador_id=2,
        is_treino=True,
        coluna_identificadora="Numero de aluno"
    )

    mock_get_ds.return_value = ds

     # Define sessão simulada
    with client.session_transaction() as sess:
        sess["user"] = "test_user"
        sess["id"] = 2 
        sess["tipo_utilizador"] = "Data Scientist"

    response = client.post("/Modelacao/NovoModelo/create", data={
        "ds.caminho": ds.caminho,
        "nome_modelo": "ModeloTesteKFold",
        "threshold": "0.5",
        "validacao": "kfold",
        "kfold_n": "5",
        "colunas_remover": ["Nacionality"],
        "dataset_id": "1",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"metricas" in response.data or b"Matriz" in response.data

def testar_desempenho_previsao():
    try:
        print(f"[INFO] Início do teste de desempenho - Modelo {15}, Dataset {23}")
        
        # 1. Carregar modelo e dataset do BD
        modelo_obj = ModeloPreditivo.query.get(15)
        dataset_obj = Dataset.query.get(23)

        if not modelo_obj or not dataset_obj:
            print("[ERRO] Modelo ou Dataset não encontrado.")
            return

        # 2. Desserializar modelo e normalizador
        modelo = pickle.loads(modelo_obj.modelo_serializado)
        normalizador = pickle.loads(modelo_obj.normalizador_serializado)

        # 3. Carregar e preparar o dataset
        df = pd.read_csv(dataset_obj.caminho)
        features = json.loads(modelo_obj.features_utilizadas)
        X = df[features]
        X_scaled = normalizador.transform(X)

        # 4. Medir tempo de previsão
        inicio = time.time()
        y_pred = modelo.predict(X_scaled)
        fim = time.time()

        tempo_total = fim - inicio
        print(f"[RESULTADO] Tempo de execução da previsão: {tempo_total:.4f} segundos")
        print(f"[INFO] Previu {len(y_pred)} registos.")

        assert tempo_total < 3 

    except Exception as e:
        print(f"[ERRO] Falha no teste de desempenho: {str(e)}")
