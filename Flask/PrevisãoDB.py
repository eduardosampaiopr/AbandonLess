from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship

import pandas as pd

import pickle
from io import BytesIO
import json

from ModeloDB import getModelsByID, prever
from DataSetDB import getDatasetByID, obter_delimitador

class Previsao(db.Model):
    __tablename__ = 'previsao'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    resultados = Column(JSON)
    modelo_id = Column(Integer, ForeignKey('modelo_preditivo.id'))
    dataset_execucao_id = Column(Integer, ForeignKey('dataset.id'))
    utilizador_id = Column(Integer, ForeignKey('utilizador.id'))
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    modelo = relationship('ModeloPreditivo', back_populates='previsoes')
    dataset_execucao = relationship('Dataset', back_populates='previsoes')
    utilizador = relationship('Utilizador', back_populates='previsoes')

def getPrevByUser(user_id):
    try:
        search_db = Previsao.query.filter_by(utilizador_id = user_id).all()
        if search_db:
            return search_db
        return None
    except Exception as e:
        print(f"Erro ao obter previsões do utilizador {user_id}: {e}")

def getPrevByID(id):
    try:
        previsao = Previsao.query.filter_by(id=id).first()
        if previsao:
            return previsao
        return None
    except Exception as e:
        print(f"Erro ao obter previsão com ID : {id}: {e}")

def makePrev(model_id, dataset_id, user_id):
    modeloObj = getModelsByID(model_id)
    dsObj = getDatasetByID(dataset_id)

    coluna_id = dsObj.coluna_identificadora
    if not coluna_id :
        print(f"A coluna de identificação '{coluna_id}' não foi encontrada no dataset.")
        return False

    previsao = prever(modeloObj, dsObj.caminho, coluna_id)

    nova_prev = Previsao(
        resultados = previsao,
        modelo_id = model_id,
        dataset_execucao_id = dataset_id,
        utilizador_id = user_id
    )

    try: 
        db.session.add(nova_prev)
        db.session.commit()
        return nova_prev.id
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao guardar previsão: {e}")
        return False
    
def remPrev(id):
    try:
        db_search = Previsao.query.filter_by(id = id).first()
        if db_search:
            db.session.delete(db_search)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover previsão com ID {id}: {e}")



    