from flask import Flask, session, request, render_template, url_for, redirect, flash
from flask_mysqldb import MySQL

app = Flask(__name__)

#configurações necessárias para usar o mysql:
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_filmlandia'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#chave para critografia de cookies na sessão
app.config['SECRET_KEY'] = 'superdificil'

conexao = MySQL(app)

def get_cursor():
    return conexao.connection.cursor()



@app.route('/')
def index():
    return render_template('pages/index.html')



@app.route('/meusfilmes/', methods=['POST', 'GET'])
def meusfilmes():
    usuario_atual = session.get('usu_id') #Obtendo o usuário atual da sessão
    if not usuario_atual:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("""
        SELECT fil_id, fil_nome, fil_genero 
        FROM tb_filmes
        WHERE fil_usu_id = %s
    """, (usuario_atual,))

    filmes = cursor.fetchall()  # Pega todos os filmes do usuário atual

    return render_template('pages/meusfilmes.html', filmes=filmes)




@app.route('/veravaliacao/<int:fil_id>', methods=['GET'])
def veravaliacao(fil_id):
    # Obtendo o usuário atual da sessão (supondo que esteja armazenado)
    usuario_atual = session.get('usu_id')
    
    if not usuario_atual:
        # Se o usuário não estiver logado, redirecione para a página de login
        return redirect(url_for('login'))

    cursor = get_cursor()
    
    #Consulta SQL para pegar a avaliação do usuário atual para o filme específico:
    cursor.execute("""
        SELECT ava_nota, ava_comentario, fil_nome, fil_genero 
        FROM tb_avaliacoes
        JOIN tb_filmes ON ava_fil_id=fil_id
        WHERE ava_fil_id = %s AND ava_usu_id = %s
    """, (fil_id, usuario_atual,))
    
    avaliacao = cursor.fetchone()  #Retorna uma tupla com os valores da consulta

    if avaliacao:
        #Desempacotando os valores retornados:
        nota, comentario, nome_filme, genero_filme = avaliacao
    else:
        nota, comentario, nome_filme, genero_filme = None, 'Nenhuma avaliação encontrada.', '', ''

    return render_template('pages/veravaliacao.html', nota=nota, comentario=comentario, nome_filme=nome_filme, genero_filme=genero_filme)




@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'usu_id' in session: #se o usuário está logado
        return redirect (url_for('meusfilmes')) #vai para a lista de filmes

    if request.method == 'GET': #metodo get 
        return render_template('pages/login.html')
    else: #metodo post, ou seja preencheu o formulário de login
        nome = request.form['nome']
        senha = request.form['senha']
        cursor = get_cursor()
        cursor.execute("SELECT usu_nome, usu_senha FROM tb_usuarios WHERE usu_nome=%s AND usu_senha=%s ", (nome, senha,))
        cursor.execute("SELECT usu_id FROM tb_usuarios WHERE usu_nome=%s AND usu_senha=%s", (nome, senha,))
        usuario = cursor.fetchone()
        if usuario:  # Se o usuário for encontrado
            session['usu_id'] = usuario['usu_id']  # Armazena o ID do usuário na sessão
            return redirect(url_for('meusfilmes'))  # Redireciona para a página de filmes
        else:
            return "SENHA INCORRETA ou usuário não cadastrado"  # Se o login falhar


    

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    #Se já está logado, redireciona para a página de filmes
    if 'usu_id' in session:
        return redirect(url_for('meusfilmes'))  

    if request.method == 'GET':
        return render_template('pages/cadastro.html')
    else: #Se o método for post:
        nome = request.form['nome']
        senha = request.form['senha']
        cursor = get_cursor()

        cursor.execute("SELECT usu_nome FROM tb_usuarios WHERE usu_nome=%s", (nome,))
        if not cursor.fetchone(): #se o usuário não tiver no db
            cursor.execute("INSERT INTO tb_usuarios (usu_nome, usu_senha) VALUES (%s, %s)", (nome, senha,)) #cadastra ele 
            conexao.connection.commit()

            
            cursor.execute("SELECT usu_id FROM tb_usuarios WHERE usu_nome=%s", (nome,)) #Pega o ID do novo usuário inserido
            novo_usuario = cursor.fetchone() 

            session['usu_id'] = novo_usuario['usu_id'] #armazena o id na sessão
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('meusfilmes'))
        else:
            flash('usuário já existe!', 'error')
            return redirect(url_for('login')) 




@app.route('/addfilme', methods=['POST', 'GET'])
def addfilme():
    # Verifica se o usuário está logado
    usuario_atual = session.get('usu_id')
    if not usuario_atual:
        # Redireciona para a página de login se o usuário não estiver logado
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome_filme = request.form['adicionar-nome-filme']
        genero_filme = request.form['genero-filme']

        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO tb_filmes (fil_nome, fil_genero, fil_usu_id) 
            VALUES (%s, %s, %s)
        """, (nome_filme, genero_filme, usuario_atual)) # Inserindo o filme no db
        conexao.connection.commit()

        #exibe a mensagem e redireciona para a lista de filmes
        flash('Filme adicionado com sucesso!', 'success')
        return redirect(url_for('meusfilmes'))

    else:
        return render_template('pages/addfilme.html')




@app.route('/removefilme', methods=['POST', 'GET'])
def removefilme():
    usuario_atual = session.get('usu_id')
    if not usuario_atual:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome_filme = request.form['excluir-nome-filme']

        cursor = get_cursor()
        cursor.execute("""
            SELECT fil_id FROM tb_filmes
            WHERE fil_nome = %s AND fil_usu_id = %s
        """, (nome_filme, usuario_atual))
        
        filme = cursor.fetchone()

        if filme:
            fil_id = filme['fil_id']
            # Exclui apenas a avaliação do usuário atual
            cursor.execute("DELETE FROM tb_avaliacoes WHERE ava_fil_id = %s AND ava_usu_id = %s", (fil_id, usuario_atual))
            # Exclui o filme se não houver mais avaliações associadas a ele
            cursor.execute("""
                DELETE FROM tb_filmes 
                WHERE fil_id = %s AND fil_usu_id = %s AND NOT EXISTS (
                    SELECT 1 FROM tb_avaliacoes WHERE ava_fil_id = %s
                )
            """, (fil_id, usuario_atual, fil_id))
            conexao.connection.commit()
            
            flash('Avaliação removida com sucesso! O filme será removido se não houver mais avaliações associadas.', 'success')
        else:
            flash('Filme não encontrado ou você não tem permissão para removê-lo.', 'error')

        return redirect(url_for('meusfilmes'))
    else:
        return render_template('pages/removefilme.html')




@app.route('/logout', methods=['POST', 'GET'])
def logout():
    #Verifica se o usuário está logado
    if 'usu_id' in session:
        session.pop('usu_id', None)#remove o id do usuário e retorna None caso a chave usu_id não exista(evita erros)
        flash('Logout realizado com sucesso!', 'success')
    else:
        flash('Nenhum usuário logado!', 'error')
    return redirect(url_for('index')) #após o logout redireciona para a página de logout
