################################################################################
# Script Created by William Leatham IV in August of 2019
# Description:
# This program was created to grab single station temperature, dewpoint, 
# relative humidity, feel like temperature, wind speed and wind gust from IEM. 
# The temperature and dew point information is in degrees Celsius. The feel like
# temperature is in degrees Fahrenheit per IEM. Wind speed and gusts are in mph. 
################################################################################
# Import a few modules required
import urllib2
import datetime
import math 
import pandas as pd
from pandas import Timestamp
import os, sys
import csv
import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt


# Will need to remove this when running this program outside of this instance
# of AWS. 
os.chdir(r'/home/ec2-user/environment/Projects/Climate/')

# The station identifier
station = 'DYT'

# The times that we are interested in
syear = '1975'
eyear = '2019'
smont = '1'
emont = '8'
sdays = '1'
edays = '10'
iem_url = 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station='+station+'&data=tmpc&data=dwpc&data=relh&data=feel&data=sped&data=gust_mph&year1='+syear+'&month1='+smont+'&day1='+sdays+'&year2='+eyear+'&month2='+emont+'&day2='+edays+'&tz=Etc%2FUTC&format=onlycomma&latlon=no&missing=M&trace=T&direct=no&report_type=1&report_type=2'

# This method simply calculates the difference between two data points. Then 
# returns the difference between the two. 
def diff(datapoint1, datapoint2):
    diff = datapoint1 - datapoint2
    return diff
    
# This method converts a value from celsius to fahrenheit
def celstofahr (celsius):
    if celsius == np.nan:
        fahrenheit = np.nan
    else:
        fahrenheit = celsius * 1.8 + 32
    return fahrenheit
    
def exist (value):
    if value == 'M':
        datavalue = np.nan
    else:
        datavalue = float(value)
    return datavalue
# This method sends a request to a url along and checks to see if there are any 
# error codes from our request. If there is an error then it is displayed.

def main():
    req = urllib2.Request(iem_url)
    try:
        response = urllib2.urlopen(req)
        parseCSV = csv.reader(response)
# This next line moves past the header
        header1 = next(parseCSV)
    except urllib2.HTTPError as error:
        if error.code == 400: print error.msg
    data = []
    for row in parseCSV:
        stid = row[0]
        time = row[1]
        temp = celstofahr(exist(row[2]))
        dewp = celstofahr(exist(row[3]))
        relh = exist(row[4])
        feel = exist(row[5])
        wind = exist(row[6])
        gust = exist(row[7])
        data.append([time,temp,dewp,relh,feel])
        
# Putting in the column headers
    col_names = ['Date','Temp (F)','Dewpoint (F)','Relative Humidity (%)','Apparent Temp (F)']
# Putting the dataset together with column headers
    df = pd.DataFrame(data, columns = col_names)
# Converting the 'Date' column to a datetime
    df['Date']=pd.to_datetime(df['Date'],format='%Y-%m-%d %H:%M',utc=True)
# Setting the date as the index and converting it to local time.
    df.set_index('Date',inplace=True)
    df.index = df.index.tz_convert('America/Chicago')
# Doing the calculations of the data set to get the daily average.
    dailymax = df.groupby([(df.index.year),(df.index.month),(df.index.day)]).max()
    dailymin = df.groupby([(df.index.year),(df.index.month),(df.index.day)]).min()
    dailyavg = (dailymax+dailymin)/2.0
    dailyavg_df = pd.DataFrame(dailyavg)
    
# Reformatting things to calculate the monthly average.
    timechange = pd.DataFrame(dailyavg_df.index.values.tolist(), columns=['year','month','day'])
    dailyavg_df.index = pd.to_datetime(timechange,format='%Y-%m-%d')
    monthly_avg = dailyavg_df.groupby([(dailyavg_df.index.year),(dailyavg_df.index.month)]).mean()
    
    monthly_dat = pd.DataFrame(monthly_avg)
    monthly_dat.index.names = ['year','month']
    data_columns = ['Temp (F)','Dewpoint (F)','Relative Humidity (%)','Apparent Temp (F)']
    monthly_dat = monthly_dat.reset_index(drop=False)

    monthly_dat['YYYY-MM']= monthly_dat['year'].map(str)+'-'+monthly_dat['month'].map(str)
    monthly_dat['YYYY-MM']= pd.to_datetime(monthly_dat['YYYY-MM'])

# Grabbing the data from 1980 to 2010 so we can calculate the 30 year normal
    normals_df = dailyavg_df[(dailyavg_df.index.year >= 1980) & (dailyavg_df.index.year <= 2010)]
    normals_30y = normals_df.groupby([normals_df.index.month]).mean()
#    normals_30y.to_csv(station+'-data.csv',mode='a')
    plt.figure()
    for n in range (int(syear),int(eyear)):
        plotting_df = pd.DataFrame(monthly_dat[(monthly_dat['year'] == n)])
        plt.plot(plotting_df['month'],plotting_df['Temp (F)'],label=n,lw=0.5)
    plt.plot(normals_30y.index,normals_30y['Temp (F)'],'--',label='1980-2010 normal',lw=1.5,color='black')
    plt.xlim(1,12)
    plt.ylim(0,80)
    plt.xlabel('Month')
    plt.ylabel('Temperature (F)')
    plt.savefig('tmp.png')
main()