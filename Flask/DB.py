from Main import db

class Utilizador(db.Model):  
    __tablename__ = "utilizadores"

    ID_utilizador = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nome = db.Column(db.String(60), nullable=False)
    Tipo = db.Column(db.String(30), nullable=False)
    nome_utilizador = db.Column(db.String(30), unique=True, nullable=False)
    passw = db.Column(db.String(200), nullable=False)  

    def __init__(self, Nome, Tipo, nome_utilizador, passw):
        self.Nome = Nome
        self.Tipo = Tipo
        self.nome_utilizador = nome_utilizador
        self.passw = passw  

    def __str__(self):
        return f'{self.Nome} encontrado'


def loginDB(user, password):
    try:
        db_search = Utilizador.query.filter(
            Utilizador.nome_utilizador == user,
            Utilizador.passw == password  
        ).first()
        return db_search
    except Exception as e:
        print(f"Erro no login: {e}")
        return None

def getUserByID(ID):
    try:
        db_search = Utilizador.query.filter(
            Utilizador.ID_utilizador == ID
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

def createUser(nome, nome_utilizador, passw, tipo_utilizador, ):
    try:
        new_user = Utilizador(nome, tipo_utilizador, nome_utilizador, passw)
        db.session.add(new_user)
        db.session.commit()  # Corrigido o commit
        print(f"Usuário {new_user.Nome} criado com sucesso!")
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao criar Utilizador: {e}")

def remUser(ID):
    try:
        user = getUserByID(ID)
        if not user:
            print(f"Erro: Nenhum usuário encontrado com ID {ID}")
            return False
        db.session.delete(user)
        db.session.commit()
        print(f"Utilizador {ID} removido com sucesso!")
        return True
        
    except Exception as e:
        db.session.rollback() 
        print(f"Erro ao eliminar Utilizador: {e}")
        return False
