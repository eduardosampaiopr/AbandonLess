from Main import app
from flask import render_template, session, url_for, redirect, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os, pandas as pd

from UtilizadorDB import *
from DataSetDB import *
from ModeloDB import *
from PrevisãoDB import *

app.config["UPLOAD_FOLDER"] = "uploads"

@app.route("/", methods=["POST", "GET"])
def login():
    session.pop("user", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    session.pop("tipo_utilizador", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    if request.method == "POST":
        username = request.form["user"]
        password = request.form["password"]

        user = loginDB(username)

        if user:
           
            if not user.password.startswith("pbkdf2:sha256"):  
                # Atualizar a senha na BD para um formato criptografado
                hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
                user.password = hashed_password
                try:
                    db.session.commit()  # SALVANDO no banco corretamente
                    print(f"Senha do utilizador {username} atualizada para formato seguro.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao atualizar senha: {e}")
                    flash("Erro ao atualizar senha. Tente novamente.", "danger")
                    return redirect(url_for("login"))
                
            if check_password_hash(user.password, password):
                session["user"] = username
                session["tipo_utilizador"] = user.tipo_utilizador
                session["id"] = user.id
    
    else:
        flash("Nome de utilizador ou senha inválidos.", "danger")
            
    if "user" in session:
        if session["tipo_utilizador"] == "Administrador":
            return redirect(url_for("adminMain", username = session["user"]))
        else:
            return redirect(url_for("ConjIndex"))
    return render_template("Login.Html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("tipo_utilizador", None)
    return redirect(url_for("login"))


#Módulo de Admnistração
@app.route("/AdminIndex-<string:username>")
def adminMain(username):
    if "user" in session:
        allUsers = getUsers()
        return render_template("/Admnistração/tabela_adm.html", users = allUsers, nome = session["user"])
    else:
        return redirect(url_for("login"))


@app.route("/<int:user_id>Detalhes")
def userDetails(user_id):
    if "user" in session:
        user = getUserByID(user_id) 
        if user:
            return render_template("/Admnistração/user.html", user=user)
        else:
            return "Utilizador não encontrado", 404
    else:
        return redirect(url_for("login"))
    
@app.route("/<int:user_id>EditarUtilizador", methods=['GET', 'POST'])
def userEdit(user_id):
    if "user" in session:
        user = getUserByID(user_id) 
        if user:

            if request.method == 'POST':
                # dados do formulário
                nome = request.form["Nome"]
                nome_utilizador = request.form["nome_utilizador"]
                passw = request.form["passw"]
                passw_conf = request.form["passw_conf"]
                tipo_utilizador = request.form["TiposUtilizadores"]
                email=request.form["email"]

                if checkUsernames(nome_utilizador, exclude_user_id= user_id):
                    flash("Este nome de utilizador já está em uso.", "danger")
                    return redirect(request.url)
                
                if passw:
                    if not passw_conf:
                        flash("Por favor confirme a password.", "danger")
                        return redirect(request.url)
                    if passw != passw_conf:
                        flash("As senhas não coincidem. Tente novamente.", "danger")
                        return redirect(request.url)
                    user.password = generate_password_hash(passw, method="pbkdf2:sha256", salt_length=16)
            
                user.nome = nome
                user.username = nome_utilizador
                user.tipo_utilizador = tipo_utilizador
                user.email = email

                try:
                    db.session.commit()
                    return redirect(url_for('userDetails', user_id=user.id, flash="Alterações guardadas com sucesso." "success"))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Erro ao guardar alterações: {e}", "danger")

            return render_template("/Admnistração/user_edit.html", user = user)
        else:
            return "Utilizador não encontrado", 404
    else:
        return redirect(url_for("login"))
  

@app.route("/Admin-<string:username>/NovoUtilizador", methods=['GET', 'POST'])
def userCreate(username):

    if "user" in session:

        if request.method == 'POST':
            nome = request.form["Nome"]
            nome_utilizador = request.form["nome_utilizador"]
            passw = request.form["passw"]
            passw_conf = request.form["passw_conf"]
            tipo_utilizador = request.form["TiposUtilizadores"]
            email = request.form["email"]

            if not nome or not nome_utilizador or not passw or not passw_conf or not tipo_utilizador:
                flash("Por favor, preencha todos os campos.", "error")
                return redirect(url_for('userCreate', username = session['user'])) 
            
            if checkUsernames(nome_utilizador):
                    flash("Este nome de utilizador já está em uso.", "danger")
                    return redirect(request.url)
                
            if passw != passw_conf:
                    flash("As senhas não coincidem. Tente novamente.", "danger")
                    return redirect(request.url)
            
            hashed_password = generate_password_hash(passw, method="pbkdf2:sha256", salt_length=16)
        
            try:
                createUser(nome, email , nome_utilizador, hashed_password, tipo_utilizador)
                print("UTILIZADOR CRIADO COM SUCESSO")
                return redirect(url_for('adminMain', username = session['user']))
            except Exception as e:
                flash(f"Ocorreu um erro ao criar o utilizador: {e}", "danger")
                return redirect(request.url)
        return render_template('Admnistração/user_new.html')
            
    else: 
        return redirect(url_for("login"))

@app.route("/removerUtilizador/<int:user_id>", methods=["POST"])
def removeUser(user_id):
    if "user" in session:
        if remUser(user_id):
            return jsonify({"success": True, "message": "Utilizador removido com sucesso!"})
        else:
            return jsonify({"success": False, "message": "Utilizador não encontrado."})
    return jsonify({"success": False, "message": "É preciso estar logado."})


#Módulo de Conjunto De Dados  
@app.route("/ConjuntosDeDados")
def ConjIndex():
    if "user" in session:
        allDatasets = getDatasets(session["id"])
        return render_template("ConjuntoDeDados/conjuntodedados.html", datasets = allDatasets, current_page="ConjuntosDeDados")
    else: 
        return redirect(url_for("login"))


@app.route("/ConjuntosDeDados/NovoConjunto", methods=["POST", "GET"])
def NovoDataset():
    if "user" in session:
        if request.method == "POST":
            if "file" not in request.files:
                flash("Nenhum Ficheiro Submetido.", "error")
                return redirect(request.url)

            upload_file = request.files["file"]
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], upload_file.filename)

            if upload_file.filename == "":
                flash("Ficherio sem nome.", "error")
                return redirect(request.url)
            
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])

            # Ler o ficheiro para validação
            try:
                upload_file.seek(0)
                texto_ficheiro = TextIOWrapper(upload_file, encoding='utf-8')
                reader = csv.reader(texto_ficheiro)

                # COUNT de registos
                registos = list(reader)
                num_registos = len(registos)
                cabecalho = registos[0] if registos else [] #Obter cabeçalho

                #Verificar se existe uma coluna Target
                if "Target" in cabecalho:
                    pass
                else:
                    flash(f"Não existe nenhuma coluna chamada 'Target' neste Dataset", "danger")
                    upload_file.seek(0)
                    return redirect(request.url)
                # Se todas as validações passarem, guardar o ficheiro e os dados na base de dados
                upload_file.save(file_path)
            except Exception as e:
                flash(f"Erro ao processar o ficheiro: {e}", "error")
                return redirect(request.url)

            createDataset(num_registos, session["id"], upload_file.filename, os.path.join(app.config["UPLOAD_FOLDER"], upload_file.filename))
                

        return render_template("ConjuntoDeDados/novoConj.html", current_page="ConjuntosDeDados")
    else: 
        return redirect(url_for("login"))

@app.route("/ConjuntosDeDados/<int:dataset_id>")
def verDataset(dataset_id):
    if "user" in session:
        dataset = getDatasetByID(dataset_id)
        session["dataset_id"] = dataset_id
        print(f"ID do dataset: {dataset_id}")
        if dataset:
            page = int(request.args.get("page", 1))
            per_page = 50  
            start_row = (page - 1) * per_page

            try:
                df = pd.read_csv(dataset.caminho, delimiter= ';', skiprows=range(1, start_row + 1), nrows=per_page,
                                  encoding='utf-8', on_bad_lines='skip')
                header = pd.read_csv(dataset.caminho, delimiter= ';', nrows=0, encoding='utf-8').columns.tolist()

                total_rows = sum(1 for _ in open(dataset.caminho)) - 1  # -1 para excluir o cabeçalho
                total_pages = (total_rows + per_page - 1) // per_page
                return render_template("ConjuntoDeDados/vercsv.html", 
                                   nome_ficheiro=dataset.nome,
                                   dataset_id=dataset.id,
                                    header=header,
                                    dados=df.values,
                                    page=page,
                                    total_pages=total_pages, current_page="ConjuntosDeDados2")
            except Exception as e:
                try:
                    df = pd.read_csv(dataset.caminho, delimiter= ',', skiprows=range(1, start_row + 1),
                                      nrows=per_page, encoding='utf-8', on_bad_lines='skip')
                    header = pd.read_csv(dataset.caminho, nrows=0, delimiter= ',', encoding='utf-8').columns.tolist()

                    total_rows = sum(1 for _ in open(dataset.caminho)) - 1  # -1 para excluir o cabeçalho
                    total_pages = (total_rows + per_page - 1) // per_page
                    return render_template("ConjuntoDeDados/vercsv.html", 
                                    nome_ficheiro=dataset.nome,
                                    dataset_id=dataset.id,
                                    header=header,
                                    dados=df.values,
                                    page=page,
                                    total_pages=total_pages, current_page="ConjuntosDeDados2")
                except Exception as e:
                    print(f"Erro ao ler o ficheiro: {e}", "error")
                    return redirect(request.url)
            
        else:
            return "Dataset não encontrado", 404
    else: 
        return redirect(url_for("login"))

@app.route("/removerConjuntodeDados/<int:dataset_id>", methods=["POST"])
def removeDataset(dataset_id):
    if "user" in session:
        if remDataset(dataset_id):
            session.pop("dataset_id", None)
            return jsonify({"success": True, "message": "Dataset removido com sucesso!"})
        else:
            return jsonify({"success": False, "message": "Dataset não encontrado."})
    return jsonify({"success": False, "message": "É preciso estar logado."})

#Módulo de Modelação
@app.route("/Modelacao")
def modeloIndex():
    if "user" in session:
        allModels = getModels()
        return render_template("Modelacao/Modelacao.html", current_page="Modelacao")
    else: 
        return redirect(url_for("login"))