# Project-BDNR
Proyecto BDNR

# run all DB docker containers
# mongo
docker run --name mongodb -p 27017:27017 -d mongo
# cassandra
docker run --name cassandradb -p 9042:9042 -d cassandra
# dgraph
docker run --name dgraphdb -p 8080:8080 -p 9080:9080 -d dgraph/standalone:latest

# create a virtual environment
python3 -m venv venv

# activate virtual environment
source venv/bin/activate

# install requirements
pip install -r requirements.txt 

# run connect.py file to connect DB
python3 connect.py

# run populate.py to add information to your database
python3 populate.py

# run main.py to activate the server

