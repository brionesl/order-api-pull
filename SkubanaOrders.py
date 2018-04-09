# SkubanaOrders.py
# written by Luis Briones

import json
import os
import requests
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.dialects.postgresql import insert
import sys

ORDERS_ENDPOINT = 'http://assessment.skubana.com/orders'
CLUSTER_ENDPOINT = 'skubanacluster.cb3ddmx2dp4w.us-east-1.redshift.amazonaws.com:5439'
USERNAME = 'masteruser'
PASSWORD = 'SkuMaster123!'
DB = 'dev'
DB_CONN='postgres://' + USERNAME + ':' + PASSWORD + '@' + CLUSTER_ENDPOINT + '/' + DB

# Call to orders API
def get_data():
    try:
        resp = requests.get(ORDERS_ENDPOINT)
        resp.raise_for_status()
        orderdata = resp.json()
        return orderdata
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

# access specific elements in orders list depending on item type (order information or order details)
def create_list_item(orderdata, ordernumber, item_type):
    if item_type == 'order_address':
        return {
            "orderNumber": ordernumber,
            "country": orderdata.get('shipToAddress', {}).get('country', ''),
            "line1": orderdata.get('shipToAddress', {}).get('line1', ''),
            "line2": orderdata.get('shipToAddress', {}).get('line2', ''),
            "name": orderdata.get('shipToAddress', {}).get('name', ''),
            "postalCode": orderdata.get('shipToAddress', {}).get('postalCode', ''),
            "stateProvince": orderdata.get('shipToAddress', {}).get('stateProvince', '')
        }
    # using elif instead of else in case api end point adds additional item_types in the future
    elif item_type == 'order_items':
        return {
            "orderNumber": ordernumber,
            "sku": orderdata.get('sku', ''),
            "quantity": int(orderdata.get('quantity', 0))
        }
    else:
        return none

# setup sql tables
def init_tables(engine, tablename):
    global order_items_tbl, order_address_tbl

    # create db tables
    metadata = MetaData()

    order_address_tbl = Table(tablename[0], metadata,
                              Column('orderNumber', String(100), nullable=False, primary_key=True),
                              Column('country', String(100), nullable=True),
                              Column('line1', String(200), nullable=True),
                              Column('line2', String(200), nullable=True),
                              Column('name', String(200), nullable=True),
                              Column('postalCode', String(100), nullable=True),
                              Column('stateProvince', String(100), nullable=True)
                              )

    order_items_tbl = Table(tablename[1], metadata,
                            Column('orderNumber', String(100), nullable=False, primary_key=True),
                            Column('sku', String(100), nullable=False, primary_key=True),
                            Column('quantity', Integer, nullable=True)
                            )

    metadata.create_all(engine)

def main():
    # get order data
    orderdata = get_data()

    order_items = []
    order_address = []

    for order in orderdata:
        ordernumber = order.get('orderNumber', '')
        orderitems = order.get('orderItems', {})

        # get quantity and sku from orderItems list and store in order_items list
        [order_items.append(create_list_item(orderitem, ordernumber, 'order_items')) for orderitem in orderitems]

        # get order address info from shipToAddress dictionary and store in order_address list
        order_address.append(create_list_item(order, ordernumber, 'order_address'))

    try:
        engine = create_engine(DB_CONN)
        if not engine.dialect.has_table(engine, 'order_address') and not engine.dialect.has_table(engine, 'order_item'):
            init_tables(engine, ['order_address', 'order_item']) # on first run no staging tables are needed
        else:
            init_tables(engine, ['order_address_stg', 'order_item_stg']) # staging tables to store new data

        conn = engine.connect()

        conn.execute(insert(order_items_tbl).values(order_items))
        conn.execute(insert(order_address_tbl).values(order_address))

        # for subsequent runs, data is added to the staging tables and only new data is inserted into the final tables
        if engine.dialect.has_table(engine, 'order_address_stg') and engine.dialect.has_table(engine, 'order_item_stg'):
            conn.execute('insert into order_address select * from order_address_stg stg where stg.ordernumber not in (select ordernumber from order_address)')
            conn.execute('insert into order_item select * from order_item_stg stg where stg.ordernumber + stg.sku not in (select ordernumber + sku from order_item)')
            # delete staging tables
            conn.execute('drop table order_address_stg; drop table order_item_stg')

        # close connection to orders API
        conn.close()

    except (sqlalchemy.exc.SQLAlchemyError, sqlalchemy.exc.DBAPIError) as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main()

