
from pymongo import MongoClient
from cassandra.cluster import Cluster
import pydgraph

# MONGODB
_mongo_client = None
_mongo_db = None

def get_mongo_db():
    global _mongo_client, _mongo_db
    
    if _mongo_db is None:
        _mongo_client = MongoClient('localhost', 27017)
        _mongo_db = _mongo_client['social_network']
    
    return _mongo_db


def get_mongo_collection(collection_name):
    db = get_mongo_db()
    return db[collection_name]


# CASSANDRA
_cassandra_session = None

def get_cassandra_session():
    global _cassandra_session
    
    if _cassandra_session is None:
        cluster = Cluster(['localhost'], port=9042)
        _cassandra_session = cluster.connect()
        
        # Crear keyspace si no existe
        _cassandra_session.execute("""
            CREATE KEYSPACE IF NOT EXISTS social_network
            WITH replication = {
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }
        """)
        _cassandra_session.set_keyspace('social_network')
    
    return _cassandra_session


# DGRAPH
_dgraph_client = None

def get_dgraph_client():
    global _dgraph_client
    
    if _dgraph_client is None:
        stub = pydgraph.DgraphClientStub('localhost:9080')
        _dgraph_client = pydgraph.DgraphClient(stub)
    
    return _dgraph_client

# Cerrando conexiones
def close_all_connections():
    global _mongo_client, _mongo_db, _cassandra_session, _dgraph_client
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
    
    if _cassandra_session:
        _cassandra_session.shutdown()
        _cassandra_session = None
    
    if _dgraph_client:
        _dgraph_client = None

def test_connections():
    print("\nCONNECTIONS:")
    
    results = {}
    
    # MongoDB
    try:
        db = get_mongo_db()
        db.list_collection_names()
        print("MongoDB connected\n")
        results['MongoDB'] = True

    except Exception as e:
        print(f"MongoDB failed: {e}\n")
        results['MongoDB'] = False
    
    # Cassandra
    try:
        session = get_cassandra_session()
        session.execute("SELECT now() FROM system.local")
        print("Cassandra connected\n")
        results['Cassandra'] = True

    except Exception as e:
        print(f"Cassandra filed: {e}\n")
        results['Cassandra'] = False
    
    # Dgraph
    try:
        client = get_dgraph_client()
        query = "schema {}"
        txn = client.txn(read_only=True)
        txn.query(query)
        txn.discard()
        print("Dgraph connected\n")
        results['Dgraph'] = True

    except Exception as e:
        print(f"Dgraph failed: {e}\n")
        results['Dgraph'] = False
    
    return all(results.values())

# MAIN (para probar conexiones)


if __name__ == "__main__":
    if test_connections():
        print("All databases al connected!\n")
    else:
        print("Failed\n")