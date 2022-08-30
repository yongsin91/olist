import pandas as pd
import numpy as np
from olist.utils import haversine_distance
from olist.data import Olist


class Order:
    '''
    DataFrames containing all orders as index,
    and various properties of these orders as columns
    '''
    def __init__(self):
        # Assign an attribute ".data" to all new instances of Order
        self.data = Olist().get_data()

    def get_wait_time(self, is_delivered=True):
        """
        Returns a DataFrame with:
        [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]
        and filters out non-delivered orders unless specified
        """
        # Hint: Within this instance method, you have access to the instance of the class Order in the variable self, as well as all its attributes
        orders = self.data['orders'].copy()

        if is_delivered:
            orders = orders[orders['order_status']=='delivered'].copy()
        

        #convert dates from object into datetime objects
        orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
        orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'])
        orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'])

        #create new columns for the required dataframe
        orders['wait_time'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']).dt.days
        orders['expected_wait_time'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']).dt.days
        orders['delay_vs_expected'] = orders['wait_time'] - orders['expected_wait_time']
        orders.loc[orders['delay_vs_expected']<0,'delay_vs_expected'] = 0

        #change to required format
        orders['wait_time'] = orders['wait_time'].astype(float)
        orders['expected_wait_time'] = orders['expected_wait_time'].astype(float)
        orders['delay_vs_expected'] = orders['delay_vs_expected'].astype(float)
        
        orders = orders.filter(items=['order_id','wait_time','expected_wait_time','delay_vs_expected','order_status'])

        return orders


    def get_review_score(self):
        """
        Returns a DataFrame with:
        order_id, dim_is_five_star, dim_is_one_star, review_score
        """
        reviews = self.data['order_reviews'].copy()

        #conditioning for 5 star & 1 star review
        reviews['dim_is_five_star'] = np.where(reviews['review_score']==5,1,0)
        reviews['dim_is_one_star'] = np.where(reviews['review_score']==1,1,0)

        reviews = reviews.filter(items=['order_id', 'dim_is_five_star', 'dim_is_one_star', 'review_score'])

        return reviews

    def get_number_products(self):
        """
        Returns a DataFrame with:
        order_id, number_of_products
        """
        product_order = self.data['order_items'].copy()
        product_order = product_order.groupby(by = 'order_id').count()
        product_order.reset_index(inplace=True)
        product_order = product_order.filter(items=['order_id','price'])
        product_order.rename(columns= {'price':'number_of_products'}, inplace=True)

        return product_order

    def get_number_sellers(self):
        """
        Returns a DataFrame with:
        order_id, number_of_sellers
        """
        num_sellers = self.data['order_items'].copy()
        num_sellers = num_sellers.groupby(by=['order_id','seller_id']).count()
        num_sellers.reset_index(inplace=True)
        num_sellers = num_sellers.groupby(by=['order_id']).count()
        num_sellers.reset_index(inplace=True)
        num_sellers = num_sellers.filter(items=['order_id','seller_id'])
        num_sellers.rename(columns = {'seller_id':'number_of_sellers'},inplace=True)

        return num_sellers

    def get_price_and_freight(self):
        """
        Returns a DataFrame with:
        order_id, price, freight_value
        """
        p_f = self.data['order_items'].copy()
        p_f = p_f.groupby(by='order_id').sum()
        p_f.reset_index(inplace=True)
        p_f = p_f.filter(items=['order_id','price','freight_value'])
        
        return p_f

    # Optional
    def get_distance_seller_customer(self):
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        # $CHALLENGIFY_BEGIN

        # import data
        data = self.data
        orders = data['orders']
        order_items = data['order_items']
        sellers = data['sellers']
        customers = data['customers']

        # Since one zip code can map to multiple (lat, lng), take the first one
        geo = data['geolocation']
        geo = geo.groupby('geolocation_zip_code_prefix',
                          as_index=False).first()

        # Merge geo_location for sellers
        sellers_mask_columns = [
            'seller_id', 'seller_zip_code_prefix', 'geolocation_lat', 'geolocation_lng'
        ]

        sellers_geo = sellers.merge(
            geo,
            how='left',
            left_on='seller_zip_code_prefix',
            right_on='geolocation_zip_code_prefix')[sellers_mask_columns]

        # Merge geo_location for customers
        customers_mask_columns = ['customer_id', 'customer_zip_code_prefix', 'geolocation_lat', 'geolocation_lng']

        customers_geo = customers.merge(
            geo,
            how='left',
            left_on='customer_zip_code_prefix',
            right_on='geolocation_zip_code_prefix')[customers_mask_columns]

        # Match customers with sellers in one table
        customers_sellers = customers.merge(orders, on='customer_id')\
            .merge(order_items, on='order_id')\
            .merge(sellers, on='seller_id')\
            [['order_id', 'customer_id','customer_zip_code_prefix', 'seller_id', 'seller_zip_code_prefix']]
        
        # Add the geoloc
        matching_geo = customers_sellers.merge(sellers_geo,
                                            on='seller_id')\
            .merge(customers_geo,
                   on='customer_id',
                   suffixes=('_seller',
                             '_customer'))
        # Remove na()
        matching_geo = matching_geo.dropna()

        matching_geo.loc[:, 'distance_seller_customer'] =\
            matching_geo.apply(lambda row:
                               haversine_distance(row['geolocation_lng_seller'],
                                                  row['geolocation_lat_seller'],
                                                  row['geolocation_lng_customer'],
                                                  row['geolocation_lat_customer']),
                               axis=1)
        # Since an order can have multiple sellers,
        # return the average of the distance per order
        order_distance =\
            matching_geo.groupby('order_id',
                                 as_index=False).agg({'distance_seller_customer':
                                                      'mean'})

        return order_distance
        # $CHALLENGIFY_END

    def get_training_data(self,
                          is_delivered=True,
                          with_distance_seller_customer=False):
        """
        Returns a clean DataFrame (without NaN), with the all following columns:
        ['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected',
        'order_status', 'dim_is_five_star', 'dim_is_one_star', 'review_score',
        'number_of_products', 'number_of_sellers', 'price', 'freight_value',
        'distance_seller_customer']
        """
        # Hint: make sure to re-use your instance methods defined above
        result = self.get_wait_time(is_delivered).merge(self.get_review_score(), on = 'order_id', how='inner')\
                .merge(self.get_number_products(), on = 'order_id', how='inner')\
                .merge(self.get_number_sellers(), on = 'order_id', how='inner')\
                .merge(self.get_price_and_freight(), on = 'order_id', how='inner')
        
        if with_distance_seller_customer:
            result = result.merge(self.get_distance_seller_customer(), on = 'order_id', how='inner')

        result.dropna(inplace=True)
        
        return result
