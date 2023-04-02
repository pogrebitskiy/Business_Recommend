import pymongo

CLIENT = pymongo.MongoClient()
DB = CLIENT['Business_Recommend']
BUSINESSES = DB['business']
REVIEWS = DB['review']


def adj_review_score():
    """
    Adjusts the rating of each review based on the number
    of upvotes to the review

    Python logic:

    if rating < 3:
        return rating - math.log(upvotes)
    elif rating > 3:
        return rating + math.log(upvotes)
    else:
        return rating

    """
    pipeline = [
        {
            # Add field to document
            "$addFields": {
                "adjusted_score": {
                    # If statement, greater or less than 3
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$lt": ["$stars", 3]},
                                "then": {"$subtract": ["$stars",
                                                       {"$cond": [{"$gt": ["$useful", 0]}, {"$ln": "$useful"}, 0]}]}
                            },
                            {
                                "case": {"$gt": ["$stars", 3]},
                                "then": {"$add": ["$stars",
                                                  {"$cond": [{"$gt": ["$useful", 0]}, {"$ln": "$useful"}, 0]}]}
                            }
                        ],
                        "default": "$stars"
                    }
                }
            }
        }
    ]

    # Update every review in the collection using the pipeline
    REVIEWS.update_many({}, pipeline)


def avg_new_scores():
    """
    Calculates the average across all the newly adjusted scores
    """

    # Aggregate reviews by business_id
    pipeline = [
        {"$group":
             {"_id": "$business_id", "average_adj_score":
                 {"$avg": "$adjusted_score"}}}
    ]
    result = list(REVIEWS.aggregate(pipeline))

    # create list of bulk write operations
    operations = []
    for pair in result:
        operations.append(
            pymongo.UpdateOne({'business_id': pair['_id']}, {'$set': {'average_adj_score': pair['average_adj_score']}})
        )

    # perform bulk write operations
    BUSINESSES.bulk_write(operations)


def calc_credibility():
    """
    Utilized adjusted average and number of reviews to establish a credibility
    score for each business

    Formula:

    credibility = (adj_avg_score * num_reviews) / (num_reviews + 5)

    """
    pipeline = [
        {"$addFields": {
            # Add the new field
            "credibility_score": {
                # Calculate using weighted formula
                "$divide": [
                    {"$multiply": ["$average_adj_score", "$review_count"]},
                    {"$add": ["$review_count", 5]}
                ]
            }
        }
        }
    ]

    # Update each business in the collection
    BUSINESSES.update_many({}, pipeline)


def combine_coords():
    """
    Add a new field to each document, combining latitude and longitude into an array
    """

    pipeline = [
        {'$addFields': {
            'coord': ['$longitude', '$latitude']
        }
        }
    ]

    # Update all businesses in collection
    BUSINESSES.update_many({}, pipeline)


def split_categories():
    """
    Because the categories are comma delimited strings,
    we must split them into an array of strings.
    Easy with mongo $split function
    """
    pipeline = [
        {'$addFields':
            {
                'split_categories': {'$split': ['$categories', ", "]}

            }
        }
    ]

    # apply pipeline to every document
    BUSINESSES.update_many({}, pipeline)


if __name__ == '__main__':
    # Adjust each review
    adj_review_score()

    # Combine adjusted reviews per business
    avg_new_scores()

    # Calculate credibility of each business
    calc_credibility()

    # Combine the coords into an array
    combine_coords()

    # Split categories into array
    split_categories()
