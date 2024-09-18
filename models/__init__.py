from flask import Flask
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv 
from flask_mysqldb import MySQL


app = Flask(__name__)
conexao = MySQL(app)
load_dotenv('.env')

#configurações necessárias para usar o mysql:
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = getenv('PASSWORD')
app.config['MYSQL_DB'] = 'db_filmlandia'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

def get_conexao():
    return conexao.connection.cursor() #conexao com o banco

def commit_con():
    return conexao.connection.commit() #fazer commits



class User(UserMixin): #definindo a classe usuario
    _hash : str
    def __init__(self, **kwargs):
        self._id = None

        if 'usu_id' in kwargs.keys(): #id do usuario
            self._id = kwargs.keys()
        if 'usu_nome' in kwargs.keys():
            self._nome = kwargs['usu_nome'] #nome do usuario
        if 'usu_email' in kwargs.keys():
            self._email = kwargs['usu_email'] #email do usuario
        if 'usu_senha' in kwargs.keys():
            self._senha = kwargs['usu_senha'] #senha(hash) do usuario
        
    # 5 - sobresrever get id do UserMixin
    def get_id(self):
        return str(self._id)
    
    # ----------métodos para manipular o banco--------------#
    def save(self):   #Salvar os dados  
        cursor = get_conexao() 
        cursor.execute("INSERT INTO tb_usuarios(usu_nome, usu_email, usu_senha) VALUES (%s, %s, %s)", (self._nome, self._email, self._senha))
        # salva o id no objeto recem salvo no banco
        self._id = cursor.lastrowid
        commit_con()
        cursor.close()
        return True
    
    @classmethod
    def get(cls,user_id): #pegar os dados de um usuário
        cursor = get_conexao()
        cursor.execute("SELECT * FROM tb_usuarios WHERE usu_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            loaduser = User(nome=user['usu_nome'] , senha=user['usu_senha'])
            loaduser._id = user['usu_id']
            return loaduser
        else:
            return None
    
    @classmethod
    def exists(cls, nome): #Verificar se usário existe
        cursor = get_conexao()
        cursor.execute("SELECT * FROM tb_usuarios WHERE usu_nome = %s", (nome,))
        user = cursor.fetchone()
        cursor.close()
        if user: #melhorar esse if-else
            return True
        else:
            return False
    
    @classmethod
    def all(cls): #Pegar todos os dados
        cursor = get_conexao
        cursor.execute("SELECT usu_id, usu_nome, usu_email FROM tb_usuarios")
        users = cursor.fetchall()
        cursor.close()
        return users
    
    @classmethod
    def get_by_nome(cls,nome): #pegar usuário pelo nome
        cursor = get_conexao()
        cursor.execute("SELECT usu_id,usu_nome,usu_email,usu_senha FROM tb_usuarios WHERE usu_nome = %s", (nome,))
        user = cursor.fetchone()
        cursor.close()
        return user