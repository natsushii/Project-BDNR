# Project-BDNR
Proyecto BDNR

# enciende todos las bases de datos
# mongo
docker run --name mongodb -p 27017:27017 -d mongo
# cassandra
docker run --name cassandradb -p 9042:9042 -d cassandra
# dgraph
docker run --name dgraphdb -p 8080:8080 -p 9080:9080 -d dgraph/standalone:latest

# crea el virtual environment 
python3 -m venv venv

# instalar los requirements
pip install -r requirements.txt 

# Corre el archivo connection.py
python3 connect.py