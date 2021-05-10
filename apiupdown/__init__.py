import os
from flask import Flask, request, abort, jsonify, send_from_directory
import logging
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback

##### Setup de diretórios e variáveis globias
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



#### LOG GERAL
@app.after_request
def apos_req(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logger.info('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response

@app.errorhandler(Exception)
def excessoes(e):
    tb = traceback.format_exc()
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, tb)
    return e.status_code




# Roda APP
if __name__ == "__main__":
    app.run()
