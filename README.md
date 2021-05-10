# flask_api_updown_auth


## Instalação
Crie um clone, baixe ou copie esse repositório.

Em seguida instale as dependências com:
```
pip3 install requirements.txt
```

Rode a aplicação com:
```
flask run
```

Por padrão a aplicação apiupdown será servida em localhost (127.0.0.1) na porta
5050. Essa porta, o modo de Debug e o ambiente utilizado podem ser configurados
no arquivo .flaskenv


## Utilização
### Retorno
As mensagens de retorno da API estão em formato JSON e seguem o padrão:
```
  {
      "msg" : "Mensagem em formato string",
      "success" : true
  }
```
Onde "msg" carrega uma mensagem e "success" um booleano de indicação de status
da requisição.

### Inserção de cartão
Para inserir o valor de um único cartão, utilizar um método POST na URL:
```
localhost:5050/insere_linha/<linha>
```

Onde <linha> é uma string de 51 colunas, dividida em:
01-01: Identificador de coluna
02-07: Numeração do Lote
08-26: Número de cartão completo

Exemplo:
```
localhost:5050/insere_linha/C2     4456897999999999
```

Retorna:
```
{
  "msg": "Inserido: 'C'-'2'-'4456897999999999'",
  "success": true
}
```

### Consulta de cartão
Para verificar se o número de cartão está presente na base de dados e ter como
retorno o seu número de identificação (id) na tabela do banco de dados, deve-se
utilizar o método GET na URL:

```
localhost:5050/consulta/<numero>
```

Onde <numero> é o número do cartão.

Exemplo:
```
localhost:5050/consulta/4456897999999999
```

Retorna:
```
{
    "id": "44",
    "success": true
}
```

Caso procure um número que não está na base, o retorno é:
```
{
    "msg": "Cartao nao encontrado na base",
    "success": false
}
```


### Envio de arquivo de texto com várias linhas
Utilizar o arquivo "arquivo.txt" padrão encontrado na pasta doc/ como base.

O parser não aceita alteração no formato apresentado. Deve chegar formatado.

Enviar o arquivo .txt através do método POST na URL:
```
http://localhost:5050/insere_arquivo/<arquivo>
```
Onde <arquivo> é o nome do arquivo para upload.

Exemplo:
```
http://localhost:5050/insere_arquivo/arquivo.txt
```

Retorna:
```
{
    "msg": "Adicionados 10 cartoes do LOTE0001.",
    "success": true
}
```
