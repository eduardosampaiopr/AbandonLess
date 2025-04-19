from Main import app
from flask import render_template, session, url_for, redirect, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os, pandas as pd
from io import BytesIO, TextIOWrapper

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
                    db.session.commit()  
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
            return redirect(url_for("previsaoIndex"))
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
        flash("Caso deseje que o Dataset seja utilizado para treino de outros modelos, por favor certifique-se que a variável objetivo tem o nome 'Target' e está é binária.", "info")
        flash("Caso o conjunto de dados contenha campos vazios, o sistema irá remover as linhas com esses campos.", "info")
        if request.method == "POST":
            if "file" not in request.files:
                flash("Nenhum Ficheiro Submetido.", "error")
                return redirect(request.url)

            upload_file = request.files["file"]

            if upload_file.filename == "":
                flash("Ficheiro sem nome.", "error")
                return redirect(request.url)

            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], upload_file.filename)

            if checkIfExists(upload_file.filename, session["id"]):
                flash("Já existe um dataset com esse nome.", "danger")
                return redirect(request.url)
            
            try:
                
                # Lê tudo para memória
                file_bytes = upload_file.read()
                buffer = BytesIO(file_bytes)

                # Deteta delimitador automaticamente
                delimitador = obter_delimitador(buffer)

                buffer.seek(0)
                df = pd.read_csv(buffer, delimiter=delimitador)

                # Verificar campos vazios e remove
                if df.isnull().values.any():
                    df = df.dropna()

                # Verificar existência da coluna 'Target'
                if 'Target'  in df.columns:
                    is_treino = True
                    if df['Target'].nunique() > 2:
                        flash("A coluna 'Target' tem mais de 2 valores distintos. O sistema só aceita variáveis objetivo binárias.", "danger")
                        return redirect(request.url)
                else:
                    is_treino = False
                    
                num_registos = df.shape[0]  # Número de linhas após remoção dos NaN

                # Guarda o ficheiro no sistema de ficheiros
                with open(file_path, 'wb') as f_out:
                    df.to_csv(f_out, index=False, encoding='utf-8')

                createDataset(num_registos, session["id"], upload_file.filename, file_path, is_treino)

            except Exception as e:
                flash(f"Erro ao processar o ficheiro: {e}", "error")
                return redirect(request.url)


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
                # Abrir o ficheiro e preparar buffer para detetar delimitador
                with open(dataset.caminho, "rb") as f:
                    file_bytes = f.read()
                    buffer = BytesIO(file_bytes)
                    delimitador = obter_delimitador(buffer)

                # Lê os dados com pandas
                buffer.seek(0)
                df = pd.read_csv(BytesIO(file_bytes), delimiter=delimitador,
                                 skiprows=range(1, start_row + 1), nrows=per_page,
                                 encoding='utf-8', on_bad_lines='skip')

                buffer.seek(0)
                header = pd.read_csv(BytesIO(file_bytes), delimiter=delimitador,
                                     nrows=0, encoding='utf-8').columns.tolist()

                total_rows = sum(1 for _ in open(dataset.caminho, encoding='utf-8')) - 1
                total_pages = (total_rows + per_page - 1) // per_page

                return render_template("ConjuntoDeDados/vercsv.html", 
                    nome_ficheiro=dataset.nome,
                    num_reg=dataset.num_registos,
                    prop = dataset.is_treino,
                    dataset_id=dataset.id,
                    header=header,
                    dados=df.values,
                    page=page,
                    total_pages=total_pages,
                    current_page="ConjuntosDeDados2"
                )
            except Exception as e:
                print(f"Erro ao ler o ficheiro: {e}")
                flash(f"Erro ao ler o ficheiro: {e}", "error")
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
    
@app.route("/Modelacao/NovoModelo", methods = ["POST", "GET"])
def novoModeloDS():
    if "user" in session:
        datasets = getTrainDataset(session["id"])
        return render_template("Modelacao/modelacao_DS.html", datasets = datasets, current_page="Modelacao")
    else: 
        return redirect(url_for("login"))
    
@app.route("/Modelacao/NovoModelo/Form", methods = ["POST", "GET"])
def novoModeloForm():
    if "user" in session:
        dataset_id = request.form.get("dataset_id")
        if not dataset_id:
            flash("Nenhum dataset selecionado.", "danger")
            return redirect(url_for("novoModeloDS"))
    
        dataset = getDatasetByID(dataset_id)

        if dataset:
            try:
                
                with open(dataset.caminho, "rb") as f:
                    file_bytes = f.read()
                    buffer = BytesIO(file_bytes)
                    delimitador = obter_delimitador(buffer)

                buffer.seek(0)
                df = pd.read_csv(buffer, delimiter=delimitador)
                columns = df.columns.tolist()

            except Exception as e:
                flash(f"Erro ao processar o ficheiro: {e}", "error")
                return redirect(request.url)
        else:
            return "Dataset não encontrado", 404

        return render_template("Modelacao/criar_modelo.html", ds_id = dataset_id, colunas_dataset = columns, current_page="Modelacao")
    else: 
        return redirect(url_for("login"))

@app.route("/Modelacao/NovoModelo/create", methods = ["POST", "GET"])
def novoModeloCreate():
    if "user" in session:
        if request.method == "POST":
            nome = request.form["nome_modelo"]
            threshold = request.form["threshold"]
            tipo_teste = request.form["validacao"]
            colunas_remover = request.form.getlist("colunas_remover")
            dataset_id = request.form["dataset_id"]

            ds = getDatasetByID(dataset_id)

            threshold = float(threshold)

            if tipo_teste == "kfold":
                kfold_n = request.form.get("kfold_n")
                kfold_n = int(kfold_n) #if kfold_n else 5
                modelo = createModelLinearRegkold(ds.caminho, nome, threshold, kfold_n, colunas_remover
                                                  , session["id"], ds.id )
    
            else:
                split_ratio = request.form.get("split_ratio") 
                split_ratio = float(split_ratio) if split_ratio else 0.8
                modelo = createModelLinearRegTrainTestSplit(ds.caminho, nome, threshold, split_ratio, colunas_remover
                                                  , session["id"], ds.id ) 
            
            if addModels(modelo):
                return jsonify({"sopa": nome, "threshold": threshold, "tipo_teste": tipo_teste, "colunas_remover": colunas_remover})

            return ("Gaita")
    else: 
        return redirect(url_for("login"))


    
#Módulo de Previsão
@app.route("/Previsao")
def previsaoIndex():
    if "user" in session:
        return render_template("Previsão/Index.html", current_page="Previsão")
    else: 
        return redirect(url_for("login"))
    
@app.route("/Previsao/NovaPrevisao", methods = ["POST", "GET"])
def novaPrev():
    if "user" in session:
        return render_template("")
    else:
        return redirect(url_for("login"))