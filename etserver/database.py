"""Database worker"""
import os
import datetime

import motor.motor_asyncio as amotor
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from . import logger
from .utils import get_current_time, query_project_cache, write_project_cache, timefmt


class MongoClientHelper:
    """Helper class for writing to mongo database"""

    def __init__(self):
        self.client = amotor.AsyncIOMotorClient(
            os.getenv("DB_HOSTNAME", "localhost"), 27017
        )
        self.db = self.client[os.getenv("ETELEMETRY_DB", "et")]
        self.requests = self.db["requests"]
        self.geoloc = self.db["geo"]

    async def is_valid(self):
        """Run mongo command to ensure valid connection"""
        try:
            await self.client.admin.command("ismaster")
            logger.info("Successful connection to mongo")
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.critical("Server is not available")
            raise

    async def insert_project(self, rip, owner, repo, project_info):
        """Insert project information into collection"""

        doc = await gen_mongo_doc(rip)

        rinfo = {
            "owner": owner,
            "repository": repo,
            "version": project_info.get("version"),
            "cached": project_info.get("cached"),
            "status_code": project_info.get("status"),
            "is_ci": project_info.get("is_ci", False),
        }
        doc.update({"request": rinfo})
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

    async def get_status(self, owner, repo, mode=None):
        project_info = await query_project_cache(owner, repo, return_stale=True)
        year = 2019
        week = 0
        response = {}
        if project_info is not None and "stats" in project_info:
            if isinstance(project_info["stats"], dict):
                lastkey = sorted(project_info["stats"])[-1]
                year, week = lastkey.split("-")
                year, week = int(year), int(week)
                response = project_info["stats"]
        startdate = datetime.datetime(year, 1, 1) + datetime.timedelta(
            weeks=max(week - 1, 0)
        )
        pipeline = [
            {
                "$match": {
                    "request.owner": owner,
                    "request.repository": repo,
                    "access_time": {"$gte": startdate.strftime(timefmt)},
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {
                            "$year": {
                                "$dateFromString": {
                                    "dateString": "$access_time",
                                    "format": "%Y-%m-%d'T'%H:%M:%SZ",
                                }
                            }
                        },
                        "week": {
                            "$week": {
                                "$dateFromString": {
                                    "dateString": "$access_time",
                                    "format": "%Y-%m-%d'T'%H:%M:%SZ",
                                }
                            }
                        },
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.year": 1, "_id.week": 1}},
        ]
        docs = {}
        async for val in self.requests.aggregate(pipeline):
            docs[f'{val["_id"]["year"]}-{val["_id"]["week"]}'] = val["count"]
        if docs:
            response.update(**docs)
        project_info["stats"] = response
        await write_project_cache(owner, repo, project_info, update=False)
        return response


async def gen_mongo_doc(ip):
    """Helper method for preparing mongo documents"""
    doc = {"access_time": await get_current_time(), "remote_addr": ip}
    return doc
