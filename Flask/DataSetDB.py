from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship

from io import TextIOWrapper
import csv

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

def createDataset(path, utilizador_ID, nome , caminho):
    # COUNT de registos
    try:
        with open(path, 'r', encoding='utf-8') as f:  # Abre o ficheiro guardado
            reader = csv.reader(f)
            num_reg = len(list(reader))
            f.seek(0)
    except Exception as e:
        print(f"Erro ao ler o ficheiro CSV: {e}")
        return False
    
    try:
        new_dataSet = Dataset(
            nome=nome,
            caminho=caminho,
            num_registos=num_reg,
            utilizador_id=utilizador_ID
        )
        db.session.add(new_dataSet)
        db.session.commit()  # Corrigido o commit
        print(f"{new_dataSet.nome} registado com sucesso!")
        return True
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao guardar o DataSet: {e}")
        return False