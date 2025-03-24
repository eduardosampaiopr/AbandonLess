from Main import app
from flask import render_template, session, url_for, redirect, request

from DB import *




@app.route("/", methods=["POST", "GET"])
def login():
    session.pop("user", "tipo_utilizador") #Remove a sessão SEMPRE, apenas par desenvolvimento
    if request.method == "POST":
        username = request.form["user"]
        password = request.form["password"]

        user = loginDB(username, password)

        if user:
            session["user"] = username
            session["tipo_utilizador"] = user.Tipo
        
    if "user" in session:
        if session["tipo_utilizador"] == "Admnistrador":
            return redirect(url_for("adminMain"))
        else:
            return redirect(url_for("prev"))
    return render_template("Login.Html")

@app.route("/AdminIndex")
def adminMain():
    if "user" in session:
        allUsers = getUsers()
        return render_template("/Admnistração/tabela_adm.html", users = allUsers)
    else:
        return redirect(url_for("login"))
    
@app.route("/Previsão")
def prev():
    return render_template("/Previsao/Index.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

