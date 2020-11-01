#!/usr/bin/env python
'''
To run this script, you may want to create your python virtual environment, and
install the missing libraries in the import if any library is missing in
your environment.

Place the source excel and this script in the same directory. Run the script in
your command line. If any errors during the upserting, the script will print out
the record

following are 2 examples that can be pass to http.put in loopback

test = {
  'name': 'mcgillc2001-5-552-ap1',
  'ipAddress': '10.98.4.27',
  'serialNo': 'CNDLJSSC0K',
  'model': 'AP 305',
  'macAddress': '20a6.cdc1.526a',
  'assetTag': '2020518',
  'state': 'In Stock',
  'group': 'mcgillc2001',
  'updatedBy': 'ansible'
}

test1 = {
  "name": None,
  "ipAddress": None,
  "serialNo": "CNDLJSSC0K",
  "model": "AP 305",
  "macAddress": "20a6.cdc1.526a",
  "assetTag": "2020518",
  "state": "In Stock",
  "group": "mcgillc2001",
  "updatedBy": "ansible"
}
'''
import urllib
from urllib.request import urlopen
import json
import pandas as pd
import requests
import numpy as np
from numpy import nan
import os
import sys

'''
Uncomment the following when loopback ssl certificate expired
'''
#import ssl

#ctx = ssl.create_default_context()
#ctx.check_hostname = False
#ctx.verify_mode = ssl.CERT_NONE

# pass arguments through command line
# dev_url = https://easapp-nccm-netcmdb-api-integration.dev.apps.mcgill.ca/api/
n = len(sys.argv)
print("Total arguments passed:", n)
print("Name of Python script:", sys.argv[0])
print("cmdb:", sys.argv[1])
print("clientid:", sys.argv[2])
print("clientsecret:", sys.argv[3])


cmdb = sys.argv[1]
client_id = sys.argv[2]
client_secret = sys.argv[3]
header = {"X-IBM-Client-Id": client_id, "X-IBM-Client-Secret": client_secret}

test = {
  "name": None,
  "ipAddress": None,
  "serialNo": "CNDLJSSC0K",
  "model": "AP 305",
  "macAddress": "20a6.cdc1.526a",
  "assetTag": "2020518",
  "state": "In Stock",
  "group": "mcgillc2001",
  "updatedBy": "ansible"
}


df = pd.read_excel('Aruba_APs.xlsx', sheet_name='Sheet1')
#fill empty fileds with 0
df = df.replace(np.nan, '0', regex = True)
src = pd.DataFrame()

src['name'] = df['APNAME']
src['ipAddress'] = df.pop('IP')
src['serialNo'] = df.pop('SERIALNUMBER')
src['model'] = df.pop('MODEL_NO')
src['macAddress'] = df.pop('MAC')
src['assetTag'] = df['MCGILLTAG'].astype(int)
src['group'] = df.pop('APGROUP')
src['updatedBy'] = "ansible"
#src['switchPortId'] = df.pop('switchPortId')
#src['locationId'] = df.pop('locationId')
src['temp_msaterview'] = df.pop('MASTERVIEW_STATUS')
src['temp_switchname'] = df.pop('SWITCHNAME')



# handle different cases of state
# apname = blank; State = "In Stock"
# apname != blank && Masterview_status = blank; State = "Installed"
# apname != blank && Masterview_status = Decommissioned; State = "In Stock"
# apname != blank && Masterview_status = New; State = "In Stock"
for i, row in src.iterrows():
    if (row['name'] == '0'):
        src.at[i,'state'] = 'In Stock'
    else:
        if (row['temp_msaterview'] == '0'):
            src.at[i,'state'] = 'Installed'       
        elif (row['temp_msaterview'] == 'Decommissioned' or row['temp_msaterview'] == 'New'):
            src.at[i,'state'] = 'In Stock'
        else:
            src.at[i,'state'] = 'Unhandled Case'

del src['temp_msaterview']

# handle switchportId
# handle missing values
df['temp'] = df['PORTNUMBER'].astype(int)
src['switchport_name'] = df['MODULE'].astype(str) + '/' + df['temp'] .astype(str)

# get switchstackId
for i, row in src.iterrows():
    if (row['switchport_name'] !='0/0'):
        get_switchstacks_url = cmdb + "switch-stacks?filter[where][name]=" + row['temp_switchname']
        #print(get_switchstacks_url)
        if('dev.' in cmdb):
            res = requests.get(url = get_switchstacks_url)
        else:
            res = requests.get(url = get_switchstacks_url, headers = header)
            #print(res.request.headers)
        if (res.text == '[]'):
            src.at[i,'switchPortId'] = '0'
        else:
            # get switchstackId
            result = res.json()
            #print(result[0]['id'])
            #print(type(result[0]['id']))
            get_switchport_url = cmdb + "switch-ports?filter[where][and][0][name]=" + row['switchport_name'] + "&filter[where][and][1][switchStackId]=" + str(result[0]['id'])
            #print(get_switchport_url)
            if('dev.' in cmdb):
                res_switchport = requests.get(url = get_switchport_url)
            else:
                res_switchport = requests.get(url = get_switchport_url, headers = header)
            result1 = res_switchport.json()
            #print(res.text)
            if (res_switchport.text != '[]'):
                result_switchport = result1[0]['id']
                #print(result_switchport)
                src.at[i,'switchPortId'] = result_switchport
            else:
                src.at[i,'switchPortId'] = '0'
    else:
        src.at[i,'switchPortId'] = '0'
 
del src['temp_switchname']
del src['switchport_name']

# handle locationKey
src['temp'] = df['BUILDCODE'].astype(int)
src['temp_buildcode'] = src['temp'].astype(str)
src['temp_apname'] = df['APNAME']

for i, row in src.iterrows():
    if(row['temp_apname'] == '0' or ':' in row['temp_apname'] or 'wanlab' in row['temp_apname'] or row['temp_apname'].count('-') < 2):
        src.at[i,'temp_floor'] = '0'
        src.at[i,'temp_room'] = '0'
    else:
        src.at[i,'temp_floor'] = row['temp_apname'].split("-")[1]
        src.at[i,'temp_room'] = row['temp_apname'].split("-")[2]
#print(src['temp_floor'])
#print(src['temp_room'])

for i, row in src.iterrows():
    if(row['temp_buildcode'] == '0' or row['temp_apname'] == '0' or ':' in row['temp_apname']):
        src.at[i,'locationKey'] = '0'
    else:
        if(row['temp_floor'] == 'g'):
            if('ap' in row['temp_room']):
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|GR00'
            elif('_' in row['temp_room']):
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|GR00|' + row['temp_room'].replace('_','-')
            else:
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|GR00|' + row['temp_room']
        elif(row['temp_floor'].startswith("ss") and len(row['temp_floor']) == 3):
            if('_' in row['temp_room']):
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'][:2] + '0' +  row['temp_floor'][2:] + '|' + row['temp_room'].replace('_','-')
            elif('ap' in row['temp_room']):
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'][:2] + '0' +  row['temp_floor'][2:]
            else:
                src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'][:2] + '0' +  row['temp_floor'][2:] + '|' + row['temp_room']
        elif('_' in row['temp_room']):
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'].zfill(4) + '|' +row['temp_room'].replace('_','-')
        elif('ap' in row['temp_room']):
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'].zfill(4)
        else:
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'].zfill(4) + '|' + row['temp_room']
#print(src.head(10))
#print(src['locationKey'])

# get locationId by locationKey
for i, row in src.iterrows():
    get_locationid_url = cmdb + "locations?filter[where][locationKey]=" + row['locationKey']
    if('dev.' in cmdb):
        res = requests.get(url = get_locationid_url)
    else:
        res = requests.get(url = get_locationid_url, headers = header)
    if (res.text == '[]'):
        src.at[i,'locationId'] = '0'
    else:
        # get locationId
        result = res.json()
        #print(result[0]['id'])
        src.at[i,'locationId'] = result[0]['id']
#print(src['locationId'])
    
del src['temp_buildcode']
del src['temp_apname']
del src['temp_floor']
del src['temp_room']
del src['temp']
del src['locationKey']
            
            
'''
To avoid error during http upserting, the script divides source APs into 4 categories:
 1.has neither switchportId nor locationId
 2.have switchportId but no locationId
 3.no switchportId but locationId
 4.have both switchportId and locationId
''' 

#src = src.replace({'0': None})
url = cmdb + "access-points/batchUpsert"
for i in src.to_dict(orient='records'):
        data = eval(json.dumps(i))
        #print('raw data:')
        new_data = {k: None if v is '0' else v for (k, v) in data.items()}
        #print(new_data)
   
        if('dev.' in cmdb):
                res = requests.put(url=url, data=new_data)
        else:
                res = requests.put(url=url, data=new_data, headers = header)
        #print('response:')
        #print(res.text)

    #print out record and its categories in the console if any errors
        if("error" in res.text):
            print('error to insert the following records:')
            print(new_data)

