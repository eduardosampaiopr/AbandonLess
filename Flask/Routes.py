from Main import app
from flask import render_template, session, url_for, redirect, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from DB import *



@app.route("/", methods=["POST", "GET"])
def login():
    session.pop("user", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    session.pop("tipo_utilizador", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    if request.method == "POST":
        username = request.form["user"]
        password = request.form["password"]
        print(f'Password: {password}')

        user = loginDB(username)

        if user:
           
            if not user.passw.startswith("pbkdf2:sha256"):  
                # Atualizar a senha na BD para um formato criptografado
                hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
                user.passw = hashed_password
                try:
                    db.session.commit()  # SALVANDO no banco corretamente
                    print(f"Senha do utilizador {username} atualizada para formato seguro.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao atualizar senha: {e}")
                    flash("Erro ao atualizar senha. Tente novamente.", "danger")
                    return redirect(url_for("login"))
                
            if check_password_hash(user.passw, password):
                session["user"] = username
                session["tipo_utilizador"] = user.Tipo
    
    else:
        flash("Nome de utilizador ou senha inválidos.", "danger")
            
    if "user" in session:
        if session["tipo_utilizador"] == "Administrador":
            return redirect(url_for("adminMain", username = session["user"]))
        else:
            return redirect(url_for("prevIndex"))
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
                
                if passw:
                    if passw != passw_conf:
                        flash("As senhas não coincidem. Tente novamente.", "danger")
                        return redirect(request.url)
                    user.passw = generate_password_hash(passw, method="pbkdf2:sha256", salt_length=16)
            
                user.Nome = nome
                user.nome_utilizador = nome_utilizador

                db.session.commit()

                flash("Alterações guardadas com sucesso.", "success")
                return redirect(url_for('userDetails', user_id=user.ID_utilizador))

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

            if not nome or not nome_utilizador or not passw or not passw_conf or not tipo_utilizador:
                flash("Por favor, preencha todos os campos.", "error")
                return redirect(url_for('userCreate', username = session['user'])) 
                
            if passw != passw_conf:
                flash("As senhas não coincidem. Tente novamente.", "danger")
                return redirect(request.url)
            
            hashed_password = generate_password_hash(passw, method="pbkdf2:sha256", salt_length=16)
        
            try:
                createUser(nome, nome_utilizador, hashed_password, tipo_utilizador)
                print("UTILIZADOR CRIADO COM SUCESSO")
                return redirect(url_for('adminMain', username = session['user']))
            except Exception as e:
                flash(f"Ocorreu um erro ao criar o utilizador: {e}", "danger")
                return redirect(request.url)
        return render_template('Admnistração/user_new.html')
            
    else: 
        return redirect(url_for("login"))

@app.route("/removeUser/<int:user_id>", methods=["POST"])
def removeUser(user_id):
    if "user" in session:
        if remUser(user_id):
            return jsonify({"success": True, "message": "Utilizador removido com sucesso!"})
        else:
            return jsonify({"success": False, "message": "Utilizador não encontrado."})
    return jsonify({"success": False, "message": "É preciso estar logado."})


#Módulo de Previsão   
@app.route("/PrevisãoIndex")
def prevIndex():
    return render_template("/Previsao/Index.html")


