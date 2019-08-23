"""Database worker"""
import os

import motor.motor_asyncio as amotor
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from . import logger
from .utils import get_current_time


class MongoClientHelper:
    """Helper class for writing to mongo database"""

    def __init__(self):
        self.client = amotor.AsyncIOMotorClient(
            os.getenv("DB_HOSTNAME", 'localhost'), 27017,
        )
        self.db = self.client[os.getenv("ETELEMETRY_DB", "et")]
        self.collection = self.db[os.getenv("ETELEMETRY_COLLECTION", "v1")]

    async def is_valid(self):
        """Run mongo command to ensure valid connection"""
        try:
            await self.client.admin.command('ismaster')
            logger.info("Successful connection to mongo")
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.critical("Server is not available")
            raise

    async def db_insert(self, request, owner, repo, version, cached, status):
        """Insert request information to db"""
        host_ip = request.remote_addr or request.ip

        document = {
            "accessTime": get_current_time(),
            "remoteAddr": host_ip,
        }

        rinfo = {
            'owner': owner,
            'repository': repo,
            'version': version,
            'cached': cached,
            'status_code': status,
            }
        document.update({'request': rinfo})
        self.collection.insert_one(document)
