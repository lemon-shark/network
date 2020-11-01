# Database Migration 
# Problem: 
To migrate Access Points data from previous database to the new one. Several fields need to manipulate and combined with the information in the new database in Python Script. 
# Action
1. This script initializes HTTP Get fetch information in the new database and combined with fields from previous databse. Then HTTP Put batch upserts large volumn of results to the new database.
2. Tested the data quality for 1%, 10%, 50%, 100% of the raw data.
# Result
All the scenarios of string manipulation are covered in the script.

