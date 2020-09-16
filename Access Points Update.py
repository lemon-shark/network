#!/usr/bin/env python

import urllib
from urllib.request import urlopen
import json
import pandas as pd
import requests
import numpy as np
from numpy import nan
#import ssl

#ctx = ssl.create_default_context()
#ctx.check_hostname = False
#ctx.verify_mode = ssl.CERT_NONE
df = pd.read_excel('Aruba_APs.xlsx', sheet_name='Sheet1')
#fill empty fileds with 0
df = df.replace(np.nan, '0', regex = True)
src = pd.DataFrame()
#print(df['APNAME'])

src['name'] = df['APNAME']
src['ipAddress'] = df.pop('IP')
src['serialNo'] = df.pop('SERIALNUMBER')
src['model'] = df.pop('MODEL_NO')
src['macAddress'] = df.pop('MAC')
src['assetTag'] = df.pop('MCGILLTAG')
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
        get_switchstacks_url = "https://easapp-nccm-netcmdb-api-integration.dev.apps.mcgill.ca/api/switch-stacks?filter[where][name]=" + row['temp_switchname']
        #print(get_switchstacks_url)
        res = requests.get(url = get_switchstacks_url)
        if (res.text == '[]'):
            src.at[i,'switchPortId'] = '0'
        else:
            # get switchstackId
            result = res.json()
            #print(result[0]['id'])
            #print(type(result[0]['id']))
            get_switchport_url = "https://easapp-nccm-netcmdb-api-integration.dev.apps.mcgill.ca/api/switch-ports?filter[where][and][0][name]=" + row['switchport_name'] + "&filter[where][and][1][switchStackId]=" + str(result[0]['id'])
            #print(get_switchport_url)
            res_switchport = requests.get(url = get_switchport_url)
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
    if(row['temp_apname'] == '0' or ':' in row['temp_apname'] or 'wanlab' in row['temp_apname']):
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
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|GR00|' + row['temp_room']
        elif(row['temp_floor'].startswith("ss") and len(row['temp_floor']) == 3):
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'][:2] + '0' +  row['temp_floor'][2:] + '|' + row['temp_room']
        else:
            src.at[i,'locationKey'] = row['temp_buildcode'] + '|' + row['temp_floor'].zfill(4) + '|' + row['temp_room']
#print(src['locationKey'])

# get locationId by locationKey
for i, row in src.iterrows():
    get_locationid_url = "https://easapp-nccm-netcmdb-api-integration.dev.apps.mcgill.ca/api/locations?filter[where][locationKey]=" + row['locationKey']
    res = requests.get(url = get_locationid_url)
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
"""
test1 = {
  "name": "mcgillc2001-5-552-ap1",
  "ipAddress": "10.98.4.27",
  "serialNo": "CNDLJSSC0K",
  "model": "AP 305",
  "macAddress": "20a6.cdc1.526a",
  "assetTag": "2020518",
  "state": "In Stock",
  "group": "mcgillc2001",
  "updatedBy": "ansible"
}"""

src_no_switchportId_locationId = pd.DataFrame()
src_no_switchportId = pd.DataFrame()
src_no_switchportId_but_locationId = pd.DataFrame()
src_switchportId_no_locationId = pd.DataFrame()
src_all = pd.DataFrame()

#print("all file")
#print(src)

src_no_switchportId_locationId = src[(src['name'] == '0') | ((src['switchPortId'] == '0') & (src['locationId'] == '0'))]
#print("2 fields are 0")
#print(src_no_switchportId_locationId)
del src_no_switchportId_locationId['switchPortId']
del src_no_switchportId_locationId['locationId']

src_switchportId_no_locationId = src[((src['switchPortId'] != '0') & (src['locationId'] == '0'))]
#print("switchport no location id")
#print(src_switchportId_no_locationId)
del src_switchportId_no_locationId['switchPortId']
del src_switchportId_no_locationId['locationId']

src_no_switchportId_but_locationId = src[((src['switchPortId'] == '0') & (src['locationId'] != '0'))]
#print("no switchport but has location id")
#print(src_no_switchportId_but_locationId)
del src_no_switchportId_but_locationId['switchPortId']

src_all = src[((src['switchPortId'] != '0') & (src['locationId'] != '0'))]
#print("full data")
#print(src_all)


url = "https://easapp-nccm-netcmdb-api-integration.dev.apps.mcgill.ca/api/access-points/batchUpsert"
#res = requests.put(url=url, data=test)
#print(res.text)

#upsert records have neither switchportId nor locationId
for i in src_no_switchportId_locationId.to_dict(orient='records'):
    #print(i)
    #print(json.dumps(i))
    #print(type(json.dumps(i)))
    data = eval(json.dumps(i))
    #print(data)
    res = requests.put(url=url, data=data)
    print(res.text)

#upsert records have switchportId but no locationId
for i in src_switchportId_no_locationId.to_dict(orient='records'):
    #print(i)
    #print(json.dumps(i))
    #print(type(json.dumps(i)))
    data = eval(json.dumps(i))
    #print(data)
    res = requests.put(url=url, data=data)
    print(res.text)
    
#upsert records have no switchportId but locationId
for i in src_no_switchportId_but_locationId.to_dict(orient='records'):
    #print(i)
    #print(json.dumps(i))
    #print(type(json.dumps(i)))
    data = eval(json.dumps(i))
    #print(data)
    res = requests.put(url=url, data=data)
    print(res.text)

#upsert records have both switchportId and locationId
for i in src_all.to_dict(orient='records'):
    #print(i)
    #print(json.dumps(i))
    #print(type(json.dumps(i)))
    data = eval(json.dumps(i))
    #print(data)
    res = requests.put(url=url, data=data)
    print(res.text)

