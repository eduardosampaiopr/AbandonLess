from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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

    utilizador = relationship('Utilizador', back_populates='modelos')
    dataset_criacao = relationship('Dataset', back_populates='modelos')
    previsoes = relationship('Previsao', back_populates='modelo')