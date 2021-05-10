import os
from flask import Flask, request, abort, jsonify, send_from_directory
import logging
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback
from flask_sqlalchemy import SQLAlchemy



##### Setup de diretórios e variáveis globias
DB = "sqlite:///db/db.sqlite"
UPLOAD_DIR = "apiupdown/uplodad"
LOG_ARQUIVO = "apiupdown/log/app.log"
LOG_TAMANHO = 100000
LOG_BACKUP = 3

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

##### Setup do Logger
logger = logging.getLogger('tdm')
handler = RotatingFileHandler(LOG_ARQUIVO, maxBytes=LOG_TAMANHO, backupCount=LOG_BACKUP)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

##### Setup da aplicação
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB
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

@app.route("/arquivos")
def lista_arquivos():
    """Endpoint para listar os arquivos no servidor"""
    arquivos = []
    for arquivo in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, arquivo)
        if os.path.isfile(path):
            arquivos.append(arquivo)
    return jsonify(arquivos)

@app.route("/arquivos/<path:path>")
def get_arquivo(path):
    """Faz donwload de um arquivo"""
    return send_from_directory(UPLOAD_DIR, path, as_attachment=True)

@app.route("/arquivos/<arquivo>", methods=["POST"])
def post_arquivo(arquivo):
    """Faz upload de um arquivo"""

    if "/" in arquivo:
        # Retorna 400 BAD REQUEST
        abort(400, "Não é permitido subdiretórios")

    with open(os.path.join(UPLOAD_DIR, arquivo), "wb") as fp:
        fp.write(request.data)

    # Retorna 201, CREATED
    return "", 201


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


def gera_banco():
    db.create_all()



#### LOG GERAL
@app.after_request
def apos_req(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logger.info('%s %s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status, response.data)
    return response

@app.errorhandler(Exception)
def excessoes(e):
    tb = traceback.format_exc()
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, tb)
    return e




# Roda APP
if __name__ == "__main__":
    app.run()
