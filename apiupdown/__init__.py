import os
from flask import Flask, request, abort, jsonify, send_from_directory
import logging
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback
from flask_sqlalchemy import SQLAlchemy
from io import StringIO


##### Setup de diretórios e variáveis globias
DB = "sqlite:///db/db.sqlite"
LOG_ARQUIVO = "apiupdown/log/app.log"
LOG_TAMANHO = 100000
LOG_BACKUP = 3


##### Setup do Logger
logger = logging.getLogger('tdm')
handler = RotatingFileHandler(LOG_ARQUIVO, maxBytes=LOG_TAMANHO, backupCount=LOG_BACKUP)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

##### Setup da aplicação
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##### Model da tabela do banco
class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linha = db.Column(db.String(80), unique=False, nullable=False)
    lote = db.Column(db.String(80), unique=False, nullable=False)
    cartao = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return "%r-%r-%r" %(self.linha, self.lote, self.cartao)



##### Rotas

@app.route('/')
def msg_teste():
    return "Servindo API..."


@app.route("/insere_linha/<linha>", methods=["POST"])
def adiciona_no_banco(linha):
    lin = " ".join(linha[0].split())
    lote = " ".join(linha[1:6].split())
    cartao = " ".join(linha[7:26].split())
    entrada = Entrada(linha=lin, lote=lote, cartao=cartao)
    db.session.add(entrada)
    db.session.commit()

    msg = { 'msg' : "Inserido: " + str(entrada),
            'success' : True }

    return jsonify(msg), 201


@app.route("/consulta/<cartao>", methods=["GET"])
def consulta_cartao(cartao):
    resposta = db.session.query(Entrada).filter_by(cartao=cartao).first()
    if resposta:
        msg = {
            'id' : str(resposta.id),
            'success' : True
        }
        return jsonify(msg), 200
    else:
        msg = {
            'msg'     : "Cartao nao encontrado na base",
            'success' : False
        }
        return jsonify(msg), 400


@app.route("/insere_arquivo/<arquivo>", methods=["POST"])
def insere_arquivo(arquivo):
    """Recebe arquivo de texto"""

    recebido = request.get_data()                   # pega stram io do arquivo de texto puro
    formatado = StringIO(recebido.decode("utf-8"))  # transforma o bytes em str e str em StringIO
                                                    # para permitir iteração

    linhas = []                                     # cria array de processamento
    for linha in formatado:                         # cria linhas em uma array retirando comentários
        linha = linha.split("//")[0]                # e novas linhas
        linha = linha.replace('\\n', '')
        linhas.append(linha)

    qtd_registros = int(linhas[0][46:51])
    lote = linhas[0][37:45]

    for i in range(1, qtd_registros):
        adiciona_no_banco(linhas[i])

    msg = {
        'msg'     : "Adicionados " + str(qtd_registros) + " cartoes do " + str(lote) + ".",
        'success' : True
    }

    return jsonify(msg), 201




def gera_banco():
    db.create_all()



#### LOG GERAL
@app.after_request
def apos_req(response):
    timestamp = strftime('[%d-%b-%Y %H:%M]')
    logger.info('%s %s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status, response.data)
    return response

@app.errorhandler(Exception)
def excessoes(e):
    tb = traceback.format_exc()
    timestamp = strftime('[%d-%b-%Y %H:%M]')
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, tb)
    msg = {
        "msg" : "Ocorreu um erro",
        "success" : False
    }
    return jsonify(msg), 500




# Roda APP
if __name__ == "__main__":
    app.run()
