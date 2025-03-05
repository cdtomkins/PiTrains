#!/usr/bin/env python3
# Customisation variables
# Expects DARWIN_WEBSERVICE_API_KEY environment variable (you will need to sign up for an API key for OpenLDBWS)
# Expects DEPARTURE_CRS_CODE environment variable (e.g. "GTW" - the departure station that we're interested in)
# Expects DESTINATION_CRS_CODE environment variable (e.g. "BTN" - the destination station that we're interested in)

import os
import syslog
from datetime import datetime, timedelta
from nredarwin.webservice import DarwinLdbSession
try:
    from blinkt import set_pixel, set_clear_on_exit, show
    GOT_BLINKT=True
except RuntimeError:
    GOT_BLINKT=False

# Initialise constants
AVAILABLELEDCOUNT = 8 # Total number of LEDs available; this should be 8 if you're using a Blinkt!
CURRENTYMD=datetime.now().strftime("%Y-%m-%d")
CURRENTTIME=datetime.now()
DARWINSESSION = DarwinLdbSession(wsdl='https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx')
DEPARTUREBOARD = DARWINSESSION.get_station_board(os.environ["DEPARTURE_CRS_CODE"],destination_crs=os.environ["DESTINATION_CRS_CODE"])

# Initialise lists
ServiceStatus = []
Services = []
LEDs = [0]*AVAILABLELEDCOUNT

train_services = DEPARTUREBOARD.train_services

# Populate ServiceStatus and Services.
# White=5=imminent/just left, Green=4=on time, yellow=3=late, blue=2=unspecified delay, red=1=cancelled, black=0=none
# We also check and deal with trains that wrap over midnight
for service in train_services:

    ServiceStatus.append((service.std, service.etd))
    STD = datetime.strptime(CURRENTYMD+service.std, '%Y-%m-%d%H:%M')

    if(service.etd=="On time"):
        if STD < CURRENTTIME:
            STD += timedelta(1)
        TimeDelta = STD-CURRENTTIME
        if(int(TimeDelta.total_seconds()/60/5)<=AVAILABLELEDCOUNT-1):
            Services.append((int(TimeDelta.total_seconds()/60/5),4))
        elif(int(TimeDelta.total_seconds()/60/5)>250):
            Services.append((0,5))

    elif(service.etd=="Delayed"):
        if STD < CURRENTTIME:
            STD += timedelta(1)
        TimeDelta = STD-CURRENTTIME
        if(int(TimeDelta.total_seconds()/60/5)<=AVAILABLELEDCOUNT-1):
            Services.append((int(TimeDelta.total_seconds()/60/5),2))
        elif(int(TimeDelta.total_seconds()/60/5)>250):
            Services.append((0,5))

    elif(service.etd=="Cancelled"):
        if STD < CURRENTTIME:
            STD += timedelta(1)
        TimeDelta = STD-CURRENTTIME
        if(int(TimeDelta.total_seconds()/60/5)<=AVAILABLELEDCOUNT-1):
            Services.append((int(TimeDelta.total_seconds()/60/5),1))

    else:
        ETD = datetime.strptime(CURRENTYMD+service.etd, '%Y-%m-%d%H:%M')
        if ETD < CURRENTTIME:
            ETD += timedelta(1)
        TimeDelta = ETD-CURRENTTIME
        if(int(TimeDelta.total_seconds()/60/5)<=AVAILABLELEDCOUNT-1):
            Services.append((int(TimeDelta.total_seconds()/60/5),3))
        elif(int(TimeDelta.total_seconds()/60/5)>250):
            Services.append((0,5))

# Syslog ServiceStatus and Services
syslog.syslog(str(ServiceStatus))
syslog.syslog(str(Services))

# Dedupe Services to create LEDs. If one time slot contains more than one
# train, the "best" LED state is set - White>Green>Yellow>Blue>Red>Black
for Service in Services:
        if(Service[1]>LEDs[Service[0]]):
            LEDs[Service[0]]=Service[1]

# Syslog LEDs
syslog.syslog(str(LEDs))

# Set Blinkt! LEDs, if we have one
if GOT_BLINKT:
    for idx,LEDToSet in enumerate(LEDs):
        if(LEDToSet==5):
            set_pixel(AVAILABLELEDCOUNT-1-idx,1,1,1)
        elif(LEDToSet==4):
            set_pixel(AVAILABLELEDCOUNT-1-idx,0,1,0)
        elif(LEDToSet==3):
            set_pixel(AVAILABLELEDCOUNT-1-idx,1,1,0)
        elif(LEDToSet==2):
            set_pixel(AVAILABLELEDCOUNT-1-idx,0,1,0)
        elif(LEDToSet==1):
            set_pixel(AVAILABLELEDCOUNT-1-idx,1,0,0)

    set_clear_on_exit(False)
    show()
# Otherwise, print them
else:
    print(str(ServiceStatus))
    print(str(Services))
    print(str(LEDs))
