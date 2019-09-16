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
        self.requests = self.db["requests"]
        self.geoloc = self.db["geo"]

    async def is_valid(self):
        """Run mongo command to ensure valid connection"""
        try:
            await self.client.admin.command('ismaster')
            logger.info("Successful connection to mongo")
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.critical("Server is not available")
            raise

    async def insert_request(
        self, rip, owner, repo, version, cached, status, geoloc=None
    ):
        """Insert request information into collection"""

        entry = {
            "access_time": await get_current_time(),
            "remote_addr": rip,
        }

        rinfo = {
            'owner': owner,
            'repository': repo,
            'version': version,
            'cached': cached,
            'status_code': status,
            }
        entry.update({'request': rinfo})
        self.requests.insert_one(entry)

    async def query_geo(self, ip):
        """Search for request IP in collection"""
        entry = await self.geoloc.find_one({"remote_addr": ip})
        return entry

    async def insert_geo(self, rip, geoloc):
        """Cache request geo information to collection"""
        entry = {
            "access_time": await get_current_time(),
            "remote_addr": rip,
        }
        entry.update(geoloc)
        self.geoloc.insert_one(entry)
