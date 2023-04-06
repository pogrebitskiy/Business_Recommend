import pymongo
from pymongo import GEOSPHERE

CLIENT = pymongo.MongoClient()
DB = CLIENT['Business_Recommend']
BUSINESSES = DB['business']
REVIEWS = DB['review']


if __name__ == '__main__':
    # Create index on geo coordinates
    BUSINESSES.create_index([("coord", GEOSPHERE)], name="coord_2dsphere")

    # Index the business_id for each review
    REVIEWS.create_index([('business_id', 1)], name='business_id_1')
