import os
from flask import Flask, request, abort, jsonify, send_from_directory
import logging
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback
from flask_sqlalchemy import SQLAlchemy
from io import StringIO
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp


##### Setup de diretórios e variáveis globias
DB = "sqlite:///db/db.sqlite"
LOG_ARQUIVO = "apiupdown/log/app.log"
LOG_TAMANHO = 100000
LOG_BACKUP = 3


##### Setup do Logger
logger = logging.getLogger("tdm")
handler = RotatingFileHandler(LOG_ARQUIVO, maxBytes=LOG_TAMANHO, backupCount=LOG_BACKUP)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

##### Setup da aplicação
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "senha-super-secreta"  # TODO passar para var de ambiente
db = SQLAlchemy(app)


##### Models para o banco de dados
class Entrada(db.Model):
    """ Modelo de entrada de dado usado no banco """
    id = db.Column(db.Integer, primary_key=True)
    linha = db.Column(db.String(80), unique=False, nullable=False)
    lote = db.Column(db.String(80), unique=False, nullable=False)
    cartao = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return "%r-%r-%r" % (self.linha, self.lote, self.cartao)


class User(object):
    """ Modelo de usuário usado no banco """
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


# TODO implementar hash nas senhas
# SETUP dos usuários teste do banco
users = [
    User(1, "admin", "admin"),
    User(2, "user", "user"),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


##### ROTAS
@app.route("/insere_linha/<linha>", methods=["POST"])
@jwt_required()
def adiciona_no_banco(linha):
    """ Adiciona uma nova linha do arquivo de texto ou digitada ao banco """
    lin = " ".join(linha[0].split())
    lote = " ".join(linha[1:6].split())
    cartao = " ".join(linha[7:26].split())
    entrada = Entrada(linha=lin, lote=lote, cartao=cartao)
    db.session.add(entrada)
    db.session.commit()

    msg = {"msg": "Inserido: " + str(entrada), "success": True}

    return jsonify(msg), 201


@app.route("/consulta/<cartao>", methods=["GET"])
@jwt_required()
def consulta_cartao(cartao):
    """ Realiza a consulta do cartão fornecido """
    resposta = db.session.query(Entrada).filter_by(cartao=cartao).first()
    if resposta:
        msg = {"id": str(resposta.id), "success": True}
        return jsonify(msg), 200
    else:
        msg = {"msg": "Cartao nao encontrado na base", "success": False}
        return jsonify(msg), 400


@app.route("/insere_arquivo/<arquivo>", methods=["POST"])
@jwt_required()
def insere_arquivo(arquivo):
    """Recebe arquivo de texto"""

    recebido = request.get_data()  # pega stream io do arquivo de texto puro
    formatado = StringIO(          # transforma o bytes em str e str em StringIO
        recebido.decode("utf-8")   # para permitir iteração
    )


    linhas = []                       # cria array de processamento
    for linha in formatado:           # cria linhas em uma array retirando
        linha = linha.split("//")[0]  # comentários e novas linhas
        linha = linha.replace("\\n", "")
        linhas.append(linha)

    qtd_registros = int(linhas[0][46:51])
    lote = linhas[0][37:45]

    for i in range(1, qtd_registros):
        adiciona_no_banco(linhas[i])

    msg = {
        "msg": "Adicionados " + str(qtd_registros) + " cartoes do " + str(lote) + ".",
        "success": True,
    }

    return jsonify(msg), 201


#### LOG GERAL
@app.after_request
def apos_req(response):
    """ Após cada request, executa o log da ação e resposta """
    timestamp = strftime("[%d-%b-%Y %H:%M]")
    logger.info(
        "%s %s %s %s %s %s %s",
        timestamp,
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
        response.status,
        response.data,
    )
    return response


@app.errorhandler(Exception)
def excessoes(e):
    """ Gerencia o que acontece com as excessões globais """
    tb = traceback.format_exc()
    timestamp = strftime("[%d-%b-%Y %H:%M]")
    logger.error(
        "%s %s %s %s %s 500 INTERNAL SERVER ERROR\n",
        timestamp,
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
    )
    msg = {"msg": "Ocorreu um erro", "success": False}
    return jsonify(msg), 500


#### CONFIGURAÇÃO DA AUTH POR JWT
def authenticate(username, password):
    """ Retorna usuário caso a password do banco e a fornecida sejam a mesma """
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode("utf-8"), password.encode("utf-8")):
        return user


def identity(payload):
    """ Retorna o ID de usuário """
    user_id = payload["identity"]
    return userid_table.get(user_id, None)


jwt = JWT(app, authenticate, identity)


#### INICIA O APP
if __name__ == "__main__":
    app.run()
