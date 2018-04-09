# Order Pull from API Endpoint

This repository contains code and other files associated with a project to fetch data from an orders API endpoint. The project was written in Python 3.6 and it uses a Redshift database to store the order data. To view and analyze the data we use Tableau 10 with a direct connection to the database


## Solution

The goal of this project was to fetch order information from an orders API endpoint and properly organize the data to enable querying and reporting.
The raw data from the API is structured as a list of 'order' dictionaries which have either key:value pairs or additional nested lists and dictionaries.

The data within these structures provide 2 pieces of information: order addresses, and order items. By storing this in 2 separate related tables, we will accomplish the organization requirement of this project.

The 3 parts of this solution are:
1. A Python script that fetches the data from the API and formats it as json objects
2. A Redshift cluster setup in AWS with user authentication and IAM roles
3. A Tableau workbook connected to the Redshift database

Future development:
While outside the scope of the requirements of this project, in order to make it a production data pipeline, an AWS Lambda function will need to be created to execute the Python code at a cadence determined by additional requirements.


### SkubanaOrders.py

This script is organized into the following parts:
* get_data function - connects to the API endpoint and converts the response into a json object
* init_tables - sets up the metadata for the sql tables that will be created or updated from the main function
* create_list_item - appends data to the appropriate dataset as the program iterates through order data
* main - calls the functions above and loads the data into the redshift database

To handle the connection to the database and the commits, the SQLAlchemy libarry was used. To ensure that duplicate records were not inserted into the 2 tables, the following approach was used:
- On first run, create the order_address and order_item tables and insert the data
- On Second and subsequent runs, 2 staging tables are created with the new data. 
- SQL statements execute to insert the new records from the staging tables but only if they don't already exist in the existing tables
- Staging tables are dropped. 


### skubanacluster

A Redshift cluster - skubanacluster - was setup in AWS (N. Virginia) with one database - dev. The IAM role given to this cluster was AmazonRedshiftFullAccess 
Below is the cluster information:
Endpoint: skubanacluster.cb3ddmx2dp4w.us-east-1.redshift.amazonaws.com
Port:5439
database: dev
Username and password will be shared through email

#### Database Objects
order_address:
       ordernumber (PK),
       country,
       line1,
       line2,
       name,
       postalcode
       stateprovince

order_item:
       ordernumber (PK),,
       sku (PK)
       quantity



### OrdersDashboard.twb

A Tableau workbook provides real time updates on the data being analyzed in this project. There are 3 worksheets and 1 dashboard which displays all worksheets. The top section of the dashboard shows the average item per order for the entire order_item table. The lower left section displays the most popular SKUs by Country and the lower right pane has the overall most popular SKUs for all countries. 

This workboook can easily be published to Tableau server for end-users to analyze the order data


## Testing

Several tests were run to validate the proper acquisition of the data. Some edge cases were tested by entering the incorrect API endpoint and cluster address/port. The program has been written to handle any foreseeable exceptions.


## Deployment

As mentioned in the Solution section, the Python program simply needs to be scheduled with a Lambda function to be fully operational.

Although Tableau was the tool used to display the results of the queries in the requirement, the data results of the query could also be shown on a custom web app with a filter for country.


## Additional Comments
Some assumptions were made when designing this solution. For example, it was unknown from the requirements what the cadence of the data pull should be. Based on real world needs, execution of the script may need to be every few minutes to a daily pull. 


## Author

* **Luis Briones** - *Initial work*
