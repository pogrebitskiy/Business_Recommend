import pandas as pd
import pymongo

CLIENT = pymongo.MongoClient()
DB = CLIENT['Business_Recommend']
BUSINESSES = DB['business']
REVIEWS = DB['review']


def filter_categories(bus_id):
    """
    Find all businesses that have a category in common with the selected business

    :param bus_id: str, ID of input business

    """
    # Access the json of the desired business
    cur_bus = BUSINESSES.find_one(
        {
            'business_id': bus_id
        }
    )

    pipeline = [
        # Get the intersection of categories between target business and every other business
        {
            '$project':
                {
                    'intersection':
                        {
                            '$setIntersection': [
                                cur_bus['split_categories'],
                                '$split_categories'
                            ]
                        },
                    'business_id': 1
                },
        },
        # Only output results have at least one category in common and are not none
        {
            '$match':
                {
                    '$and':
                        [
                            {
                                'intersection':
                                    {
                                        '$ne': []
                                    }
                            },
                            {
                                'intersection':
                                    {
                                        '$ne': None
                                    }
                            }
                        ]
                }
        }
    ]

    # Apply aggregation to entire collection
    output = list(BUSINESSES.aggregate(pipeline))

    # Create dict of {business: intersection_length} for use in recommendations
    len_dct = {}
    [len_dct.update({new_dct['business_id']: len(new_dct.get('intersection', []))}) for new_dct in output]

    # Return the intersection dict and the id of every business that has at least 1 category in common
    return len_dct, [dct['business_id'] for dct in output if dct['business_id'] != bus_id]


def find_closest(lst_of_ids, max_dist, coords):
    """
    Returns the businesses within the max_distance of the origin coords,
    sorted by the previously computed credibility score

    :param lst_of_ids: list of possible business IDs
    :param max_dist: int, maximum distance to search (meters)
    :param coords: list of origin coords [longitude, latitude]
    :return: list of businesse
    """
    # define the pipeline
    pipeline = [
        {
            # Find the businesses that are within max_dist of the origin coords
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [
                        coords[0],
                        coords[1]
                    ]
                },
                "distanceField": "distance",
                "spherical": True,
                'maxDistance': max_dist

            }
        },
        {
            # Only return businesses within the specified lst_of_ids
            '$match': {
                'business_id':
                    {
                        '$in': lst_of_ids
                    }
            }
        },
        {
            # sort the results by credibility
            "$sort": {
                "credibility_score": -1
            }
        },
    ]

    # execute the pipeline and convert result to a list
    return list(BUSINESSES.aggregate(pipeline))


def get_reviews(business_id):
    """
    Function takes in a business_id and returns a dataframe of all the corresponding reviews

    :param business_id: string, ID of input business

    """
    # match business_id
    pipeline = [{'$match': {'business_id': business_id}}]
    cursor = REVIEWS.aggregate(pipeline)
    # Build df and sort
    df = pd.DataFrame([x for x in cursor]).drop(columns=['_id', 'review_id']).sort_values(by=['adjusted_score', 'date'], ascending=False)
    return df


def make_recommendations(business_id, max_dist, location_coords=None):
    """
    Given a business_id and the max_distance, output a dataframe sorted
    in recommendation order

    :param business_id: string, ID of input business
    :param max_dist: int, max_distance to limit recommendations
    :param location_coords:(optional) origin coords to search from

    """
    # Retrieve businesses with intersecting categories and their lengths
    len_dct, common_categories = filter_categories(business_id)

    # If not origin location is specified
    if not location_coords:
        # Retrieve the coords of the input business
        coords = BUSINESSES.find_one({'business_id': business_id})['coord']
        # Build dataframe from businesses that have a common category and sorted by their credibility
        dct = pd.DataFrame(find_closest(common_categories, max_dist, coords))

    # If origin location is specified, use that instead.
    else:
        dct = pd.DataFrame(find_closest(common_categories, max_dist, location_coords))

    # Create new column that accounts for the cardinality of the intersection.
    # if a restaurant has many categories in common with the input restaurant
    # it should be recommended more
    dct['recommend_score'] = dct.apply(lambda row: row['credibility_score'] + (0.5 * len_dct[row['business_id']]),
                                       axis=1)

    # Return the dataframe, sorted by recommed_score and dropping redundant columns
    return dct.sort_values(by='recommend_score', ascending=False).reset_index(drop=True).drop(
        columns=['_id', 'is_open', 'attributes', 'split_categories', 'hours', 'coord']).head(20)


if __name__ == '__main__':
    # print(make_recommendations('jcL_qaGJiappzpnn-ifSoA', 16000))
    print(get_reviews('jcL_qaGJiappzpnn-ifSoA'))
