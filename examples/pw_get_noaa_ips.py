#!/usr/bin/env python3

"""
  The purpose of this script is to generate a local .hosts file with the current IPs
  of the active clusters the user owns.

  This script will automatically connect to the NOAA ParallelWorks gateway to retrieve
  information about the current clusters using the user's API key.

  Critical files that must exist:

    $HOME/.ssh/pw_api.key - this file must contain the API key in the first and only
                            line.  Treat this file as any secure file and place in 
                            .ssh directory.  Change permissions to mode 600.

  New files created:
    $HOME/.hosts - this is a new file created every time the script is run.  
                   Do not modify this file externally as any change will be 
                   lost.  If no active clusters exists, the file will be created
                   with one commented line.  For the hosts to be recognized,
                   the HOSTALIASES environment variable must point to this
                   file (i.e. export HOSTALIASES=$HOME/.hosts).
"""

import requests
import json
import os
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pycookiecheat import chrome_cookies
from tabulate import tabulate

import pycookiecheat

homedir = os.environ['HOME']
hostsfile = homedir + '/.hosts'
keyfile = homedir + '/.ssh/pw_api.key'

cluster_hosts = []
clusters = []
owned_clusters = []

def input_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--output_json', help='Print full json response to screen',action='store_true', required=False)
    parser.add_argument('--get_cluster', help='Print pw systems by owner', type=str, required=False)
    parser.add_argument('--owner', help='Print pw systems by owner', type=str, required=False)
    args = parser.parse_args()
    return args

args = input_args()

try:
  f = open(keyfile, "r")
  my_key = f.readline().strip()
  f.close()
except IOError: 
  print("Error: API file", keyfile, "does not appear to exist.")
  sys.exit(1)

# setup the user-specific url from which to get the data
url_resources = "https://noaa.parallel.works/api/resources?key=" + my_key
url = "https://noaa.parallel.works"

cookies = pycookiecheat.firefox_cookies(url)
#cookies = chrome_cookies(url, cookie_file='/home/tmcguinness/.config/chromium/Default/Cookies')
response = requests.get(url_resources, cookies=cookies)
json_data = json.loads(response.text)

dic_entry = {}
if response:
  if args.output_json:
      print(json.dumps(json_data,indent=4))
      sys.exit(0)
  for cluster in json_data:
    if args.get_cluster:
      if cluster["name"] == args.get_cluster:
         print(json.dumps(cluster, indent=4))
         sys.exit(0)
    if args.owner:
      if cluster["namespace"] != args.owner:
        continue
      if cluster["status"] == "on":
        cluster["status"] = cluster["state"]["masterNode"]
      owned_clusters.append([cluster["namespace"], cluster["status"], cluster["displayName"], cluster["name"]])

    if "masterNode" in cluster["state"]:
      display_name = cluster['displayName']
      name = cluster['name']
      owner = cluster['namespace']
      ip = cluster['state']['masterNode'] 
      if ip is None:
          ip = "None yet"
      entry = ' '.join([name, ip])
      clusters.append([display_name, owner, ip])
      cluster_hosts.append(entry)

  if args.owner:
    print (tabulate(owned_clusters,headers=["Owner","Status","Display Name","Name"]))
    print()
  else:  
    print (tabulate(clusters,headers=["Full Name","Owner","IP"]))
    print()
  
  # Generate the user's local .hosts file
  #with open(hostsfile, 'w+') as f:
  #  f.writelines("%s\n" % l for l in cluster_hosts)
  #  print('SUCCESS - the', hostsfile, 'was updated.')
  #f.close() 
  
else:
  print ("Connection unsuccessful - can't connect to Parallel Works NOAA gateway")
  print ("status := ", response.status_code)

