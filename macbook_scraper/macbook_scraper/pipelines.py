import motor.motor_asyncio
import os
from dotenv import load_dotenv

class MacbookScraperPipeline:
    def __init__(self):
        load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
        self.client = None
        self.db = None

    def open_spider(self, spider):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('MONGO_URL'))
        self.db = self.client[os.environ.get('DB_NAME')]

    def close_spider(self, spider):
        self.client.close()

    async def process_item(self, item, spider):
        await self.db['prices'].insert_one(dict(item))
        return item
