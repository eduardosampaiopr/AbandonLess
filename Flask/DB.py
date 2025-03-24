from Main import db

class Utilizador(db.Model):  
    __tablename__ = "utilizadores"

    ID_utilizador = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(60), nullable=False)
    Tipo = db.Column(db.String(30), nullable=False)
    nome_utilizador = db.Column(db.String(30), unique=True, nullable=False)
    passw = db.Column(db.String(200), nullable=False)  

    def __init__(self, ID, Nome, Tipo, nome_utilizador, passw):
        self.ID_utilizador = ID
        self.Nome = Nome
        self.Tipo = Tipo
        self.nome_utilizador = nome_utilizador
        self.passw = passw  

    def __str__(self):
        return f'{self.Nome} encontrado'


def loginDB(user, password):
    db_search = Utilizador.query.filter(
        Utilizador.nome_utilizador == user,
        Utilizador.passw == password  
    ).first()
    return db_search

def getUserByID(ID):
    db_search = Utilizador.query.filter(
        Utilizador.ID_utilizador == ID
    ).first()

    return db_search

def getUsers():
    db_search = Utilizador.query.all() 
    return db_search