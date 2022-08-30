import os
import pandas as pd


class Olist:
    def get_data(self):
        """
        This function returns a Python dict.
        Its keys should be 'sellers', 'orders', 'order_items' etc...
        Its values should be pandas.DataFrames loaded from csv files
        """
        # Hints 1: Build csv_path as "absolute path" in order to call this method from anywhere.
            # Do not hardcode your path as it only works on your machine ('Users/username/code...')
            # Use __file__ instead as an absolute path anchor independant of your usename
            # Make extensive use of `breakpoint()` to investigate what `__file__` variable is really
        # Hint 2: Use os.path library to construct path independent of Mac vs. Unix vs. Windows specificities

        #file path
        parent = os.path.abspath(os.path.join(__file__,os.pardir))
        grandparent = os.path.abspath(os.path.join(parent,os.pardir))
        csv_path = os.path.join(grandparent,'data/csv/')

        
        #file name list
        file_names = [ a for a in os.listdir(csv_path) if a.endswith('.csv')]

        #cleaning for dictionary name list
        remove_suffix_csv = [a[:-4] for a in file_names]
        remove_suffix_dataset = [a[:-8] if a.endswith('_dataset') else a for a in remove_suffix_csv ]
        dict_name = [a[6:] if a.startswith('olist_') else a for a in remove_suffix_dataset]

        #creating dictionary for data
        data = {}

        for name,location in zip(dict_name,file_names):
            data[name]= pd.read_csv(os.path.join(csv_path, location))
            
        return data

    def ping(self):
        """
        You call ping I print pong.
        """
        print("pong")
