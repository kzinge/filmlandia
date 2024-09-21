from flask import Flask, session, request, render_template, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from models import User, commit_con
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from flask_mail import Mail, Message


app = Flask(__name__)
load_dotenv('.env')
login_manager = LoginManager()
login_manager.init_app(app) #Configura app para trabalhar junto com flask-login
mail = Mail() #Configura app para trabalhar com flask-mail

#configurações necessárias para usar o mysql:
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = getenv('PASSWORD')
app.config['MYSQL_DB'] = 'db_filmlandia'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#configurações para o mail:
app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = getenv('USERMAIL')
app.config['MAIL_PASSWORD'] = getenv('PASSMAIL')
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False

#chave para critografia de cookies na sessão
app.config['SECRET_KEY'] = 'superdificil'

mail.init_app(app)

conexao = MySQL(app)

def get_cursor():
    return conexao.connection.cursor()


@login_manager.user_loader #Carregar usuário logado
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    return render_template('pages/index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST': #metodo post
        nome = request.form['nome']
        senha = request.form['senha']
        user = User.get_by_nome(nome)

        if user is None: # Se o login falhar
            flash("Usuário não cadastrado. <a href='" + url_for('cadastro') + "'>Cadastre-se aqui</a>", "error")
            return redirect(url_for('login')) 
        if check_password_hash(user['usu_senha'], senha):  # Se o usuário for encontrado
                login_user(User.get(user['usu_id'])) 
                return redirect(url_for('meusfilmes'))  # Redireciona para a página de filmes
        flash("Senha Incorreta", "error")
        return redirect(url_for('login'))
    
    else:
        return render_template('pages/login.html')
 

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    if request.method == 'GET':
        return render_template('pages/cadastro.html')
    else: #Se o método for post:
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])
        if not User.exists(nome): #se o usuário não tiver cadastro
            user = User(usu_nome = nome, usu_email = email, usu_senha = senha)
            user.save()
            #Enviar Email
            msg = Message(subject='Filmlandia!', 
                           sender = getenv('USERMAIL'),
                           recipients= [email])
            msg.body = 'Olá Carinha, estamos passando aqui para dizer que seu cadastro foi realizado com sucesso em Filmlandia! :)'
            mail.send(msg)
            
            # Logar o usuário depois de cadastrar
            login_user(user)
            flash('Cadastro Realizado!', 'success')
            return redirect(url_for('meusfilmes'))
        else:
            flash("Esse usuário já existe! <a href='" + url_for('login') + "'>Faça Login</a>", 'error')
            return redirect(url_for('cadastro'))
        

# ROTAS PARA OS FILMES------------------------------------------------------------------------------------------------

@app.route('/meusfilmes/', methods=['POST', 'GET'])
@login_required
def meusfilmes():
    cursor = get_cursor()
    cursor.execute("""
        SELECT fil_id, fil_nome, fil_genero 
        FROM tb_filmes
        WHERE fil_usu_id = %s
    """, (current_user._id,))

    filmes = cursor.fetchall()  # Pega todos os filmes do usuário atual

    return render_template('pages/meusfilmes.html', filmes=filmes)

@app.route('/addfilme', methods=['POST', 'GET'])
@login_required
def addfilme():

    if request.method == 'POST':
        nome_filme = request.form['adicionar-nome-filme']
        genero_filme = request.form['genero']

        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO tb_filmes (fil_nome, fil_genero, fil_usu_id) 
            VALUES (%s, %s, %s)
        """, (nome_filme, genero_filme, current_user._id)) # Inserindo o filme no db
        commit_con()
        return redirect(url_for('meusfilmes'))

    else:
        return render_template('pages/addfilme.html')


@app.route('/removefilme/<int:fil_id>', methods=['POST'])
@login_required
def removefilme(fil_id):
    filme = fil_id
    cursor = get_cursor()
    cursor.execute("""
        DELETE FROM tb_avaliacoes WHERE ava_fil_id = %s 
    """, (filme,))

    cursor.execute("""
        DELETE FROM tb_filmes WHERE fil_id = %s
    """, (filme,))

    commit_con()
    return redirect(url_for('meusfilmes'))

# ROTAS PARA AS AVALIAÇÕES ------------------------------------------------------------------------------------------------------------

@app.route('/avaliar/<int:fil_id>', methods=['POST', 'GET'])
@login_required
def avaliarfilme(fil_id):
    filme =  fil_id
    cursor = get_cursor()
    if request.method == 'GET':
        cursor.execute('SELECT fil_nome FROM tb_filmes WHERE fil_id = %s', (filme,))
        fil_nome = cursor.fetchone()['fil_nome']
        return render_template('pages/addavaliacao.html', fil_id=fil_id, fil_nome=fil_nome)
    
    if request.method == 'POST':
            comentario = request.form['comentario']
            nota = request.form['nota']

            cursor.execute('SELECT ava_fil_id FROM tb_avaliacoes WHERE ava_usu_id = %s', (current_user._id,))
            filmes_avaliados = cursor.fetchall()
            filmes_avaliados_ids = [row['ava_fil_id'] for row in filmes_avaliados]

            for id_filme in filmes_avaliados_ids:
                if id_filme == filme:
                    novo_comentario = request.form['comentario']
                    nova_nota = request.form['nota']

                    cursor.execute("""
                        UPDATE tb_avaliacoes SET ava_comentario = %s, ava_nota = %s
                        WHERE ava_fil_id = %s;
                    """, (novo_comentario, nova_nota, id_filme))
                    commit_con()
                    return redirect(url_for('veravaliacao', fil_id=filme))
            
            #Se o filme nunca foi avaliado
            cursor.execute("""
                INSERT INTO tb_avaliacoes(ava_comentario, ava_nota, ava_fil_id, ava_usu_id)
                VALUES (%s, %s, %s, %s)
            """, (comentario, nota, filme, current_user._id))
            commit_con()
            return redirect(url_for('veravaliacao', fil_id=filme))
    
@app.route('/veravaliacao/<int:fil_id>', methods=['GET'])
@login_required
def veravaliacao(fil_id):
    cursor = get_cursor()
    
    #Consulta SQL para pegar a avaliação do usuário atual para o filme específico:
    cursor.execute("""
        SELECT ava_nota, ava_comentario, fil_nome, fil_genero
        FROM tb_avaliacoes
        JOIN tb_filmes ON ava_fil_id=fil_id
        WHERE ava_fil_id = %s AND ava_usu_id = %s
    """, (fil_id, current_user._id,))
    
    avaliacao = cursor.fetchone()  #Retorna uma tupla com os valores da consulta

    if not avaliacao:
            nota = None
            filme_genero = ''
            filme_nome = ''
            filme_id = fil_id
            comentario = 'Opa! Você ainda não avaliou esse filme!'
    
    else:
        nota = avaliacao['ava_nota']
        comentario = avaliacao['ava_comentario']
        filme_nome = avaliacao['fil_nome']
        filme_genero = avaliacao['fil_genero']
        filme_id = fil_id

    return render_template('pages/veravaliacao.html', nota=nota, comentario=comentario, filme_nome=filme_nome, filme_genero=filme_genero, filme_id=filme_id)



@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))