from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


class Dataset(db.Model):
    __tablename__ = 'dataset'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    caminho = Column(String(255), nullable=False)
    num_registos = Column(Integer)
    data_upload = Column(DateTime, default=datetime.datetime.utcnow)
    utilizador_id = Column(Integer, ForeignKey('utilizador.id'))
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    utilizador = relationship('Utilizador', back_populates='datasets')
    modelos = relationship('ModeloPreditivo', back_populates='dataset_criacao')
    previsoes = relationship('Previsao', back_populates='dataset_execucao')
