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

    async def insert_project(self, rip, owner, repo, project_info):
        """Insert project information into collection"""

        doc = await gen_mongo_doc(rip)

        rinfo = {
            'owner': owner,
            'repository': repo,
            'version': project_info.get('version'),
            'cached': project_info.get('cached'),
            'status_code': project_info.get('status'),
            }
        doc.update({'request': rinfo})
        self.requests.insert_one(doc)

    async def query_geocookie(self, ip):
        """Search for request IP in collection"""
        entry = await self.geoloc.find_one({"remote_addr": ip})
        return entry

    async def insert_geo(self, rip, geoloc):
        """Cache request geo information to collection"""
        doc = await gen_mongo_doc(rip)
        doc.update(geoloc)
        self.geoloc.insert_one(doc)


async def gen_mongo_doc(ip):
    """Helper method for preparing mongo documents"""
    doc = {
        "access_time": await get_current_time(),
        "remote_addr": ip
    }
    return doc
