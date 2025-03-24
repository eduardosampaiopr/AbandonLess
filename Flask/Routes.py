from Main import app
from flask import render_template, session, url_for, redirect, request, flash


from DB import *



@app.route("/", methods=["POST", "GET"])
def login():
    session.pop("user", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    session.pop("tipo_utilizador", None) #Remove a sessão SEMPRE, apenas par desenvolvimento
    if request.method == "POST":
        username = request.form["user"]
        password = request.form["password"]

        user = loginDB(username, password)

        if user:
            session["user"] = username
            session["tipo_utilizador"] = user.Tipo
        
    if "user" in session:
        if session["tipo_utilizador"] == "Admnistrador":
            return redirect(url_for("adminMain", Username = session["user"]))
        else:
            return redirect(url_for("prevIndex"))
    return render_template("Login.Html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("tipo_utilizador", None)
    return redirect(url_for("login"))


#Módulo de Admnistração
@app.route("/AdminIndex-<string:Username>")
def adminMain(Username):
    if "user" in session:
        allUsers = getUsers()
        return render_template("/Admnistração/tabela_adm.html", users = allUsers, nome = session["user"])
    else:
        return redirect(url_for("login"))


@app.route("/<int:user_id>Details")
def userDetails(user_id):
    if "user" in session:
        user = getUserByID(user_id) 
        if user:
            return render_template("/Admnistração/user.html", user=user)
        else:
            return "Utilizador não encontrado", 404
    else:
        return redirect(url_for("login"))
    
@app.route("/<int:user_id>Edit", methods=['GET', 'POST'])
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
                
                if passw != passw_conf:
                    flash("As senhas não coincidem. Tente novamente.", "danger")
                    return redirect(request.url)
            
                user.Nome = nome
                user.nome_utilizador = nome_utilizador
                user.passw = passw  # Aqui seria uma boa prática criptografar a senha antes de salvar
                user.Tipo = tipo_utilizador

                db.session.commit()

                flash("Alterações salvas com sucesso.", "success")
                return redirect(url_for('userDetails', user_id=user.ID_utilizador))

            return render_template("/Admnistração/user_edit.html", user = user)
        else:
            return "Utilizador não encontrado", 404
    else:
        return redirect(url_for("login"))
  
@app.route("/<int:user_id>-<string:Username>remove")
def userElim(user_id, Username):
    return ("Removido com sucé")

#Módulo de Previsão   
@app.route("/PrevisãoIndex")
def prevIndex():
    return render_template("/Previsao/Index.html")


