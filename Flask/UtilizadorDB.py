from Main import db
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


class Utilizador(db.Model):
    __tablename__ = 'utilizador'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    tipo_utilizador = Column(String(50))
    username = Column(String(255), nullable=False, unique=True)
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    
    datasets = relationship('Dataset', back_populates='utilizador')
    modelos = relationship('ModeloPreditivo', back_populates='utilizador')
    previsoes = relationship('Previsao', back_populates='utilizador')

    def __init__(self, nome, email, password, tipo_utilizador, username):
        self.nome = nome
        self.email = email
        self.password = password
        self.tipo_utilizador = tipo_utilizador
        self.username = username


def loginDB(user):
    try:
        db_search = Utilizador.query.filter(
            Utilizador.username == user, 
        ).first()
        return db_search
    except Exception as e:
        print(f"Erro no login: {e}")
        return None

def getUserByID(ID):
    try:
        db_search = Utilizador.query.filter(
            Utilizador.id == ID
        ).first()
        return db_search
    except Exception as e:
        print(f"Erro ao encontrar utilizador por ID: {e}")
        return None
    
def getUsers():
    try:
        db_search = Utilizador.query.all() 
        return db_search
    except Exception as e:
        db.session.rollback()  # Corrigido o rollback
        print(f"Erro ao encontrar utilizador: {e}")
        return None

def createUser(nome, email, username, password, tipo_utilizador, ):
    try:
        new_user = Utilizador(nome, email, password, tipo_utilizador, username)
        db.session.add(new_user)
        db.session.commit()  # Corrigido o commit
        print(f"{new_user.Nome} criado com sucesso!")
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao criar Utilizador: {e}")

def remUser(ID):
    try:
        user = getUserByID(ID)
        if not user:
            print(f"Erro: Nenhum utilizador encontrado com ID {ID}")
            return False
        db.session.delete(user)
        db.session.commit()
        print(f"Utilizador {ID} removido com sucesso!")
        return True
        
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao eliminar Utilizador: {e}")
        return False
    
def checkUsernames(username, exclude_user_id=None):
    try:
        query = Utilizador.query.filter(Utilizador.username == username)
        if exclude_user_id:
              query = query.filter(Utilizador.id != exclude_user_id)

        return query.first()
    except Exception as e:
        print(f"Erro ao encontrar utilizador por ID: {e}")
        return None