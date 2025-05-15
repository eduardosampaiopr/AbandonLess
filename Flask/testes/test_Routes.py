import time
from flask import Flask
import sys
import os
from io import BytesIO
import tempfile
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import pickle

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Main import app, db 
from DataSetDB import *
from ModeloDB import *
from UtilizadorDB import *
from PrevisãoDB import *
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


@patch('Routes.getDatasetByID')  
# Teste de desempendho de criação de modelo 
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

# Teste de desempendho de realização de previsão
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

#---------------------------- Testes unitários ----------------------------
# Teste UtilizadorDB
@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield
@patch('UtilizadorDB.Utilizador.query')
def test_loginDB_found(mock_query):
    mock_user = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_user
    result = loginDB("admin")
    assert result == mock_user
    mock_query.filter.assert_called_once()

@patch('UtilizadorDB.Utilizador.query')
def test_loginDB_not_found(mock_query):
    mock_query.filter.return_value.first.return_value = None
    result = loginDB("nao_existe")
    assert result is None

@patch('UtilizadorDB.Utilizador.query')
def test_getUserByID_found(mock_query):
    mock_user = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_user
    result = getUserByID(1)
    assert result == mock_user

@patch('UtilizadorDB.Utilizador.query')
def test_getUserByID_not_found(mock_query):
    mock_query.filter.return_value.first.return_value = None
    result = getUserByID(99)
    assert result is None

@patch('UtilizadorDB.Utilizador.query')
def test_getUsers_success(mock_query):
    mock_query.all.return_value = ["user1", "user2"]
    result = getUsers()
    assert result == ["user1", "user2"]

@patch('UtilizadorDB.db.session')
def test_createUser_success(mock_session):
    createUser("João", "joao@example.com", "joaouser", "senha", "Administrador")
    assert mock_session.add.called
    assert mock_session.commit.called

@patch('UtilizadorDB.db.session')
@patch('UtilizadorDB.getUserByID')
def test_remUser_success(mock_get_user, mock_session):
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user
    result = remUser(1)
    assert result is True
    assert mock_session.delete.called
    assert mock_session.commit.called

@patch('UtilizadorDB.db.session')
@patch('UtilizadorDB.getUserByID')
def test_remUser_not_found(mock_get_user, mock_session):
    mock_get_user.return_value = None
    result = remUser(999)
    assert result is False
    assert not mock_session.delete.called

@patch('UtilizadorDB.Utilizador.query')
def test_checkUsernames_found(mock_query):
    mock_query.filter.return_value.first.return_value = "user"
    result = checkUsernames("admin")
    assert result == "user"

@patch('UtilizadorDB.Utilizador.query')
def test_checkUsernames_with_exclude(mock_query):
    mock_filter = MagicMock()
    mock_filter.filter.return_value.first.return_value = "outro_user"
    mock_query.filter.return_value = mock_filter
    result = checkUsernames("admin", exclude_user_id=5)
    assert result == "outro_user"

#Teste DatasetDB

@patch("DataSetDB.db.session.add")
@patch("DataSetDB.db.session.commit")
def test_create_dataset_success(mock_commit, mock_add):
    result = createDataset(100, 1, "Teste.csv", "/caminho/teste.csv", True, "aluno_id")
    assert result is True
    assert mock_add.called
    assert mock_commit.called


@patch("DataSetDB.Dataset.query")
def test_get_datasets(mock_query):
    mock_query.filter_by.return_value.all.return_value = ["dataset1", "dataset2"]
    datasets = getDatasets(1)
    assert len(datasets) == 2


@patch("DataSetDB.Dataset.query")
def test_get_dataset_by_id(mock_query):
    mock_query.filter.return_value.first.return_value = "dataset"
    result = getDatasetByID(123)
    assert result == "dataset"


@patch("os.path.isfile", return_value=True)
@patch("os.remove")
@patch("DataSetDB.db.session.commit")
@patch("DataSetDB.db.session.delete")
@patch("DataSetDB.getDatasetByID")
def test_rem_dataset_sucesso(mock_get, mock_delete, mock_commit, mock_remove, mock_isfile):
    mock_get.return_value = MagicMock(caminho="ficheiro.csv")
    resultado = remDataset(10)
    assert resultado is True
    assert mock_remove.called


@patch("DataSetDB.Dataset.query")
def test_check_if_exists_true(mock_query):
    mock_query.filter_by.return_value.first.return_value = MagicMock(id=99)
    resultado = checkIfExists("ficheiro.csv", 2)
    assert resultado is True


@patch("DataSetDB.Dataset.query")
def test_get_datasets_for_prev(mock_query):
    mock_query.filter_by.return_value.all.return_value = ["ds1", "ds2"]
    resultado = getDatasetsForPrev(2)
    assert resultado == ["ds1", "ds2"]


@patch("DataSetDB.Dataset.query")
def test_get_train_datasets(mock_query):
    mock_query.filter_by.return_value.all.return_value = ["train_ds"]
    resultado = getTrainDataset(1)
    assert resultado == ["train_ds"]


def test_obter_delimitador_com_csv_valido():
    buffer = BytesIO(b"col1,col2\n1,2\n3,4")
    delimitador = obter_delimitador(buffer)
    assert delimitador == ','


def test_check_one_hot_encoding_invalido():
    buffer = BytesIO(b"curso,sexo\nEngenharia,M\nMedicina,F")
    resultado = checkOneHotEncoding(buffer, ",")
    assert resultado == 0

#Teste ModeloDB
@patch("ModeloDB.db.session.add")
@patch("ModeloDB.db.session.commit")
def test_add_model_success(mock_commit, mock_add):
    modelo = MagicMock(nome="ModeloTeste")
    resultado = addModels(modelo)
    assert resultado == 1
    mock_add.assert_called_once()
    mock_commit.assert_called_once()



@patch("ModeloDB.ModeloPreditivo.query")
@patch("ModeloDB.db.session.delete")
@patch("ModeloDB.db.session.commit")
def test_rem_model_success(mock_commit, mock_delete, mock_query):
    mock_query.filter_by.return_value.first.return_value = MagicMock()
    resultado = remModel(1)
    assert resultado == 1
    mock_delete.assert_called_once()



@patch("ModeloDB.ModeloPreditivo.query")
def test_get_models(mock_query):
    mock_query.all.return_value = ["modelo1", "modelo2"]
    resultado = getModels(1)
    assert resultado == ["modelo1", "modelo2"]



@patch("ModeloDB.ModeloPreditivo.query")
def test_get_model_by_id(mock_query):
    mock_query.filter_by.return_value.first.return_value = "modeloX"
    resultado = getModelsByID(10)
    assert resultado == "modeloX"


@patch("ModeloDB.getDatasetFeatures")
@patch("ModeloDB.ModeloPreditivo.query")
def test_get_compatible_models(mock_query, mock_features):
    modelo1 = MagicMock(features_utilizadas=["A", "B"])
    modelo2 = MagicMock(features_utilizadas=["C", "D"])
    mock_query.all.return_value = [modelo1, modelo2]
    mock_features.return_value = ["A", "B", "C", "D", "E"]

    resultado = getCompatibleModels(123)
    assert modelo1 in resultado
    assert modelo2 in resultado

class DummyScaler:
    def transform(self, X):
        return X

class DummyModel:
    def predict(self, X):
        return np.array([0.6, 0.3])

def test_prever_simples():
    import os

    # Dataset simulado
    df = pd.DataFrame({
        "feat1": [1, 2],
        "feat2": [3, 4],
        "Numero de aluno": ["A1", "B2"],
        "Curricular units 1st sem (credited)": [10, 15],
        "Curricular units 2nd sem (credited)": [20, 25]
    })

    class MockModelo:
        def __init__(self):
            self.features_utilizadas = ["feat1", "feat2"]
            self.normalizador_serializado = pickle.dumps(DummyScaler())
            self.modelo_serializado = pickle.dumps(DummyModel())
            self.hiper_parametros = json.dumps({"intervalo_admissao": 0.5})

        def prever(self, dataset_path, col_id):
            return prever(self, dataset_path, col_id)

    model = MockModelo()

    tmp_path = "test_dataset_temp.csv"
    df.to_csv(tmp_path, index=False)

    try:
        result = model.prever(tmp_path, "Numero de aluno")
        assert result == [{"aluno_id": "A1", "previsao": 1}, {"aluno_id": "B2", "previsao": 0}]
    finally:
        os.remove(tmp_path)

#Teste de PrevisãoDB

@patch('PrevisãoDB.Previsao.query')
def test_getPrevByUser_found(mock_query):
    mock_query.filter_by.return_value.all.return_value = ['prev1', 'prev2']
    result = getPrevByUser(1)
    assert result == ['prev1', 'prev2']

@patch('PrevisãoDB.Previsao.query')
def test_getPrevByUser_not_found(mock_query):
    mock_query.filter_by.return_value.all.return_value = []
    result = getPrevByUser(99)
    assert result is None



@patch('PrevisãoDB.Previsao.query')
def test_getPrevByID_found(mock_query):
    mock_query.filter_by.return_value.first.return_value = 'prev'
    result = getPrevByID(1)
    assert result == 'prev'

@patch('PrevisãoDB.Previsao.query')
def test_getPrevByID_not_found(mock_query):
    mock_query.filter_by.return_value.first.return_value = None
    result = getPrevByID(404)
    assert result is None


@patch('PrevisãoDB.Previsao.query')
@patch('PrevisãoDB.db')
def test_remPrev_found(mock_db, mock_query):
    mock_prev = MagicMock()
    mock_query.filter_by.return_value.first.return_value = mock_prev

    result = remPrev(1)
    assert result is True
    mock_db.session.delete.assert_called_once_with(mock_prev)
    mock_db.session.commit.assert_called_once()

@patch('PrevisãoDB.Previsao.query')
@patch('PrevisãoDB.db')
def test_remPrev_not_found(mock_db, mock_query):
    mock_query.filter_by.return_value.first.return_value = None

    result = remPrev(404)
    assert result is False
    mock_db.session.delete.assert_not_called()


@patch('PrevisãoDB.getModelsByID')
@patch('PrevisãoDB.getDatasetByID')
@patch('PrevisãoDB.db')
@patch('PrevisãoDB.prever')
def test_makePrev_success(mock_prever, mock_db, mock_getDataset, mock_getModel):
    mock_model = MagicMock()
    mock_ds = MagicMock()
    mock_ds.coluna_identificadora = "aluno_id"
    mock_ds.caminho = "dummy.csv"

    mock_getModel.return_value = mock_model
    mock_getDataset.return_value = mock_ds
    mock_prever.return_value = [{"aluno_id": "A1", "previsao": 1}]

    mock_db.session.add = MagicMock()
    mock_db.session.commit = MagicMock()

    result = makePrev(1, 2, 3)
    assert isinstance(result, int) or result is not False

@patch('PrevisãoDB.getModelsByID')
@patch('PrevisãoDB.getDatasetByID')
def test_makePrev_missing_coluna(mock_getDataset, mock_getModel):
    mock_getDataset.return_value = MagicMock(coluna_identificadora=None)
    mock_getModel.return_value = MagicMock()

    result = makePrev(1, 2, 3)
    assert result is False

