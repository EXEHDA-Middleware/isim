## Framework iSim
### Ciência de Situação dos Reservatórios do SANEP no Ambiente Computacional da IoT Explorando Tendências em Contextos

Este trabalho está sendo desenvolvido no escopo do convênio existente entre o Serviço Autônomo de Saneamento de Pelotas (SANEP) e a Universidade Católica de Pelotas (UCPel), o qual tem como premissa atender diferentes demandas de gerenciamento daquela autarquia com o emprego de abordagens técnico-científicas. Neste sentido, este trabalho irá contribuir com o Projeto SANEP-I²MF (*SANEP Interactive IoT-based Multisensor Framework*), o qual visa prover suporte para o acompanhamento dos artefatos eletromecânicos do SANEP, utilizando a Internet das Coisas (IoT), enquanto tecnologia que permite a integração e comunicação entre objetos, formando uma infraestrutura de rede composta por softwares, sensores e atuadores, que podem coletar e trocar dados de forma distribuída. Mais especificamente, a abordagem iSim tem o objetivo de prover o acompanhamento dos reservatórios do SANEP, registrando informações provenientes de diferentes sensores. A expectativa é explorar a Ciência de Contexto e Situação, onde cada reservatório poderá ter um conjunto específico de regras para processamento das suas informações sensoriadas. 

#### Descrição dos Diretórios

**bot-telegram:**  
Neste diretório ...

**context-server:**

# iSim Context Server

## Descrição

O projeto consiste de um software desenvolvido na Linguagem Python que desempenha a gestão de dados provenientes de dispositivos IoT por meio do protocolo MQTT. Ele recebe continuamente dados de sensores, os armazena banco de dados persistente e oferece a capacidade de criar regras de disparo de alertas com a ajuda de um Bot Telegram concebido para operar de forma integrada.

## Pré-requisitos

- Linguagem Python 3
- Gerenciador de Banco de Dados MySQL
- PM2 Process Management

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

**gateway:**  
Neste diretório estão ...
