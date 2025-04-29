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

def makePrev(model_id, dataset_id, user_id):
    modeloObj = getModelsByID(model_id)
    dsObj = getDatasetByID(dataset_id)

    previsao = prever(modeloObj, dsObj.caminho)
    resultados_json = previsao.tolist()

    nova_prev = previsao(
        resultados_json,
        model_id,
        dataset_id,
        user_id
    )




    