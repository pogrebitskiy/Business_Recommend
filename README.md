# Business Recommend
### By: Elvin Cheng, Julia Favis, Jason Fuji, Kristina Fujimoto, David Pogrebitskiy

### Setup:
1. Download Yelp data from https://www.yelp.com/dataset.
2. Start local Mongo instance using `mongo-server`.
3. Create a new database.
4. Use import utilities of your choosing to import the following:
   1. `yelp_academic_dataset_business.json` with collection name `business`.
   2. `yelp_academic_dataset_review.json` with collection name `review`.

5. Execute the `preprocessing.py` script to preprocess Yelp dataset in MongoDB.
6. Execute the `index_creation.py` script to create indices for lookup and aggregation.
7. Start up front-end dashboard by executing `UI.py`.


### Recommendations:
1. Front-end dashboard located at `UI.py`.
   1. Enter a `business_id` and specify the max distance (meters).
3. Generate visualizations by running the `viz.ipynb` notebook.


