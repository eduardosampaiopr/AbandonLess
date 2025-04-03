from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


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