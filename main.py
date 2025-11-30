import falcon.asig
import logging
from connect import get_mongo_db, get_cassandra_session, get_dgraph_client, test_connections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware:
    async def process_request(self, req, resp):
        logger.info(f"Request: {req.method} {req.uri}")

    async def process_response(self, req, resp, resource, req_succeeded):
        logger.info(f"Response: {resp.status} for {req.method} {req.uri}")

app = falcon.asgi.App(middleware=[LoggingMiddleware()])
