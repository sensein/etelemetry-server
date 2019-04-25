"""Backend worker"""
import os

import motor.motor_asyncio as masyncio

from .utils import get_current_time


class MongoClientHelper:
    """Helper class for managing mongodb operations"""
    client = masyncio.AsyncIOMotorClient('localhost', 27017)
    db = client[os.environ.get("ETELEMETRY_DB", "et")]
    collection = db[os.environ.get("ETELEMETRY_COLLECTION", "v1")]

    async def db_insert(self, host, owner, repo, version, cached, status):
        """Insert request information to db"""
        document = {
            "accessTime": get_current_time(),
            "remoteAddr": host,
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
