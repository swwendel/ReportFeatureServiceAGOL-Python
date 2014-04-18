"""
Title: ReportFeatureServices.py
Description: Creates a log the Members found in AGOL for an organization and
provides information about each member.
Version: 1.2
Author: Stephanie Wendel
Created: 12/27/2013
Updated: 1/2/2014
Tags: Log, AGOL, Admin Tasks, Membership information, Organization Information.
"""

# Modules needed
import urllib, urllib2, httplib
import json
import socket
import os, sys, time
from time import localtime, strftime


"""
Variable Setup: These are the Admin variables used in this script. Changes
should be made to username and password that reflect an ADMIN user found within
the organization.
"""
# Admin Variables to be changed.
username = ""
password = ""
# portalName - include Web Adaptor name if it has one or use arcgis.com for AGOL
# organizational account.
portalName = 'http://www.arcgis.com'

# Host name will be generated based on the computer name. No Changes need to be
# made.
hostname = "http://" + socket.getfqdn()


"""
Setup of Monkey Patch, Token, Logs, and Service Requests.
"""
# Monkey Patch httplib read
# code from http://bobrochel.blogspot.co.nz/2010/11/bad-servers-chunked-encoding-and.html
def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            return e.partial

    return inner

httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)


# Generate Token
if "arcgis.com" in portalName:
    token_URL = 'https://www.arcgis.com/sharing/generateToken'
else:
    token_URL = "{0}/sharing/generateToken".format(portalName)
token_params = {'username':username,'password': password,'referer': hostname,'f':'json'}
token_request = urllib2.Request(token_URL, urllib.urlencode(token_params))
token_response = urllib2.urlopen(token_request)
token_string = token_response.read()
token_obj = json.loads(token_string)
token = token_obj['token']


# log functions: createLog - builds basic log structure, Log - adds value to log
def createLog(OrgName, name, headers=None, fType=".txt"):
    location = sys.path[0]
    timesetup = strftime("%m_%d_%Y", localtime())
    logfile = OrgName +"_" + name + "_"+ timesetup + fType
    f = open(logfile, 'wb')
    if headers != None:
        f.write(headers)
        f.write("\n")
    f.close()
    return logfile

def Log(logfile, message):
    f = open(logfile, 'ab')
    f.write(message)
    f.write("\n")
    f.close()


# Define basic http request
def makeRequest(URL, PARAMS={'f': 'json','token': token}):
    request = urllib2.Request(URL, urllib.urlencode(PARAMS))
    response = urllib2.urlopen(request).read()
    JSON = json.loads(response)
    return JSON


"""
Portal Information: Builds log about organization properties. Finds Organization
ID for further use in script. Also builds basic building block of finding users
in the organziation. Included in this log is the total number of users.
"""
# Find Organization ID
print 'Starting orgnaization log'
url = '{0}/sharing/rest/portals/self'.format(portalName)
JVal = makeRequest(url)
OrgID = JVal['id']
OrgName = JVal['name'].replace(' ', '_')
OrgLogFile = createLog(OrgName, "OrgInfo")
Log(OrgLogFile, "OrganizationName: {}\r".format(OrgName))
Log(OrgLogFile, "OrganizationID: {}\r\r".format(OrgID))
Log(OrgLogFile, "Current Organization Properties:\r")
if "arcgis.com" in portalName:
    AvailCredits = (JVal['subscriptionInfo'])['availableCredits']
    Log(OrgLogFile, "Available Credits: {}\r".format(AvailCredits))


# Find Organization users
def orgUsers(start=1):
    global OrgID, token
    url = '{0}/sharing/rest/portals/{1}/users'.format(portalName, OrgID)
    params = {'start':start, 'num': 100, 'f': 'json','token': token}
    userrequest = makeRequest(url, params)
    return userrequest

totalusers = orgUsers()['total']
Log(OrgLogFile, "Total users: {}\r".format(totalusers))

print 'Finished processing organization information'


"""
Membership information: Creates a CSV file to track membership information about
users in this organization. Properties include: fullName, email, username, role,
number of feature Services under that username.
"""
# user search - example, for finding feature service count
def userSearch(username, Stype=None):
    global token
    url = '{0}/sharing/rest/search'.format(portalName)
    if Stype == None:
        q='owner:{0}'.format(username)
    else:
        q='type:{0} AND owner:{1}'.format(Stype, username)
    params = {'q':q, 'num': 100, 'f': 'json','token': token}
    searchRequest = makeRequest(url, params)
    return searchRequest

# Process Membership information in CSV format
# Create log for membership
print 'Starting Membership log processing'
MemberslogFile = createLog(OrgName, 'Membership', 'Member, Email, Username, Role, HostedFS, ItemTotal', '.csv')

# Process the first 100 users
users1 = orgUsers()['users']
for user in users1:
    full = user['fullName']
    email = user['email']
    username = user['username']
    role = user['role']
    FScount = userSearch(username, 'Feature Service')['total']
    itemCount = userSearch(username)['total']
    Log(MemberslogFile, "{0}, {1}, {2}, {3}, {4}, {5}".format(full, email, username, role, FScount, itemCount))

# Process the rest of the users over 100
newStart = 0
while totalusers > 100:
    newStart += 100
    users2 = orgUsers(newStart)['users']
    for user2 in users2:
        full = user2['fullName']
        email = user2['email']
        username = user2['username']
        role = user2['role']
        FScount = userSearch(username, 'Feature Service')['total']
        itemCount = userSearch(username)['total']
        #print "{0}'s full account is {1} and associated email is {2}".format(full, username, email)
        Log(MemberslogFile, "{0}, {1}, {2}, {3}, {4}, {5}".format(full, email, username, role, FScount, itemCount))


    totalusers -= 100



print "\nReporting is Done"