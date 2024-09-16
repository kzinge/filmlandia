from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mysql'  # Use o banco de dados padrão para executar o SQL
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

conexao = MySQL(app)

def execute_sql_file(filename):
    with app.app_context():  #Criando o contexto da aplicação
        cursor = conexao.connection.cursor()
        with open(filename, 'r') as file:
            sql = file.read() #Lê o arquivo e armazena como uma string
            comandos_raw = sql.split(';') #Divide o conteúdo do arquivo em uma lista usando ';' como delimitador

            commands = [] #Lista para armazenar comandos SQL limpos
            for comando in comandos_raw:
                comando_limpo = comando.strip() #Remover espaços em branco no início e no fim do comando
                if comando_limpo:#Verificar se o comando não está vazio
                    commands.append(comando_limpo)#Adicionar o comando limpo à lista 'commands'

            for command in commands: #percorrendo os comandos limpos
                cursor.execute(command) #executando cada comando
        conexao.connection.commit()
        cursor.close()

if __name__ == "__main__":
    execute_sql_file('db/schema.sql')  # Caminho ajustado para o arquivo SQL
    print("Banco de dados e tabelas inicializados com sucesso!")
