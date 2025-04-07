from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship
import os
from io import TextIOWrapper
import csv
import pandas as pd

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

def createDataset(num_reg, utilizador_ID, nome , caminho):

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
    
def getDatasets(user_id):
    try:
        db_search = Dataset.query.filter_by(utilizador_id=user_id).all()
        return db_search
    except Exception as e:
        db.session.rollback()  # Corrigido o rollback
        print(f"Erro ao encontrar Datasets: {e}")
        return None
    
def getDatasetByID(id):
    try:
        db_search = Dataset.query.filter(
            Dataset.id == id
        ).first()
        return db_search
    except Exception as e:
        print(f"Erro ao encontrar dataset por ID: {e}")
        return None
    
def remDataset(id):
    try:
        ds = getDatasetByID(id)
        if ds:
            if ds.caminho and os.path.isfile(ds.caminho):
                os.remove(ds.caminho)
                print(f"Ficheiro {ds.caminho} removido com sucesso.")
            else:
                print(f"Ficheiro não encontrado ou caminho inválido: {ds.caminho}")
            db.session.delete(ds)
            db.session.commit()
            print(f'Dataset {id} removido com sucesso!')
            return True
        else:
            print(f"Erro: Nenhum dataset encontrado com ID {id}")
            return False
        
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao eliminar Dataset: {e}")
        return False
    



def obter_delimitador(buffer):
    buffer.seek(0)
    sample = buffer.read(2048).decode('utf-8', errors='ignore')
    buffer.seek(0)

    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        print(f"[Sniffer] Delimitador detetado: '{dialect.delimiter}'")
        return dialect.delimiter
    except csv.Error:
        # Fallback simples baseado em contagem
        print("[Sniffer] Erro ao detetar delimitador. Análise manual em curso...")
        if sample.count(';') > sample.count(','):
            print("[Heurística] Delimitador escolhido: ';'")
            return ';'
        else:
            print("[Heurística] Delimitador escolhido: ','")
            return ','


