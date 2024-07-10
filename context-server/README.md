# iSim Context Server

## Descrição

O projeto é uma aplicação Python que desempenha a gestão de dados provenientes de dispositivos IoT por meio do protocolo MQTT. Ele recebe continuamente dados de sensores, os armazena banco de dados persistente e oferece a capacidade de criar regras de disparo de alertas com a ajuda de um bot integrado.

## Pré-requisitos

- Python 3
- MySQL
- PM2

## Instalação

Use um dos comandos abaixo para clonar o repositório:

`git clone git@github.com:exehdamiddleware/isim.git`

ou

`git clone https://github.com/exehdamiddleware/isim.git`

Faça uma copia do .env.example e o renomeie para .env

Preencha as variaveis com os dados a serem usados e em seguida prosiga com os comandos:

- Faz o setup de dependencias e do banco interno que irá possuir os projetos, além de criar um banco padrão pronto para uso:

  `python3 context-server/setup-server.py`

- Opcionalmente rode o seguinte comando para adicionar novos projetos:

  `python3 context-server/setup/bases/index.py <PROJECT_NAME> <MYSQL_HOST> <MYSQL_USER> <MYSQL_PASSWORD> <MYSQL_DB_NAME>`

- Para rodar o projeto:

  `pm2 start context-server/pm2.config.js`
