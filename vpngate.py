#!/usr/bin/env python

"""Pick server and start connection with VPNGate (http://www.vpngate.net/en/)"""
import datetime
import argparse

import requests, os, sys, tempfile, subprocess, base64, time, csv, itertools
import random as rand
CACHE_PATH = 'vpngate.csv'

parser = argparse.ArgumentParser(description='Description.')
parser.add_argument('-r', '--random', nargs='?', type=int)
parser.add_argument('-c', '--country', nargs='?', type=str)
parser.print_usage()
args = parser.parse_args()
country = args.country
random = args.random


def get_vpn_data():
    delta = None
    if os.path.exists(CACHE_PATH):
        filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_PATH))
        today = datetime.datetime.today()
        delta = today - filemtime
    if delta is None or delta > datetime.timedelta(days=1):
        with open(CACHE_PATH, 'w') as f:
            f.write(requests.get('http://www.vpngate.net/api/iphone/').text.replace('\r', ''))


def find(servers) -> dict:
    supported = [s for s in servers if s['OpenVPN_ConfigData_Base64'] and len(s['OpenVPN_ConfigData_Base64']) > 0]

    if country:
        # desired = filter(lambda s: s['CountryShort'] and s['CountryLong'], supported)
        desired = list(filter(lambda s:
                                             country.lower() in s['CountryShort'] and s['CountryShort'].lower() or country.lower() in s['CountryLong'].lower(), desired)
                       )
        found = len(desired)
        print('Found ' + str(found) + ' servers')
        if found == 0:
            exit(1)
        winner = sorted(supported, key=lambda s: float(s['Score'].replace(',', '.')), reverse=True)[0]
        return winner
        # desired = [s for s in servers if
        #            ]
    elif random:
        # desired = supported[:random]
        return supported[rand.randint(0, random)]
    else:
        return supported[0]

def apply(winner):
    print("\n== Best server ==")
    keys=['#HostName','IP','Score','Ping']
    filtered = dict(winner)
    del filtered['OpenVPN_ConfigData_Base64']
    for (l, d) in filtered.items():
        if l == 'Speed':
            print('Speed: {0} MBps'.format(round(int(winner['Speed']) / 10 ** 6),2))
        else:
            print(l + ': ' + d)
    # print("Country: " + winner['CountryLong'])

    print("\nLaunching VPN...")
    _, path = tempfile.mkstemp()
    path = os.path.expanduser(
        "~/Library/Application Support/Tunnelblick/Configurations/VPNGate.tblk/Contents/Resources/config.ovpn")
    if not os.path.exists(path):
        print("Please add first OpenVpn connection by hand, name it 'VPNGate'")
        exit(-1);
    f = open(path, 'wb')
    f.write(base64.b64decode(winner['OpenVPN_ConfigData_Base64']))
    f.close()
    x = subprocess.call(['osascript', 'script.scpt'])
    print(x)


try:
    get_vpn_data()
    with open(CACHE_PATH, 'r') as f:
        if f.readline() == '*vpn_servers':
            f.seek(0)
        servers = csv.DictReader(f)
        winner = find(servers)
        apply(winner)
        # for row in servers:
        #     print(row)
except Exception as e:
    raise e
    # print('Cannot get VPN servers data')
    # exit(1)

