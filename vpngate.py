#!/usr/bin/env python

"""Pick server and start connection with VPNGate (http://www.vpngate.net/en/)"""
import datetime
import argparse

import requests, os, sys, tempfile, subprocess, base64, time, csv, itertools
import random as rand

CONFIG_DIRS = ["~/Library/Application Support/Tunnelblick/Configurations/",
               "/Library/Application Support/Tunnelblick/Shared/"]
CACHE_PATH = 'vpngate.csv'

parser = argparse.ArgumentParser(description='Description.')
parser.add_argument('-r', '--random', nargs='?', type=int, help='Select random row from first N rows')
parser.add_argument('-c', '--country', nargs='?', type=str, help='Country code or name. RU or Russia')
parser.add_argument('-p', '--print', type=int)
args = parser.parse_args()
country = args.country
random = args.random
if country is None and random is None:
    parser.print_usage()
    exit(0)


def get_vpn_data():
    delta = None
    if os.path.exists(CACHE_PATH):
        filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_PATH))
        today = datetime.datetime.today()
        delta = today - filemtime
    if delta is None or delta > datetime.timedelta(days=1):
        link = 'http://www.vpngate.net/api/iphone/'
        file_name = CACHE_PATH
        with open(file_name, "wb") as f:
            print("Downloading VPNs")
            response = requests.get(link, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()
        # with open(CACHE_PATH, 'w') as f:
        #     f.write(requests.get('http://www.vpngate.net/api/iphone/').text.replace('\r', ''))


def find(servers):
    supported = [s for s in servers if s['OpenVPN_ConfigData_Base64'] and len(s['OpenVPN_ConfigData_Base64']) > 0]

    if country:
        # desired = filter(lambda s: s['CountryShort'] and s['CountryLong'], supported)
        desired = list(filter(lambda s:
                              country.lower() in s['CountryShort'].lower() or country.lower() in
                              s['CountryLong'].lower(), supported)
                       )
        found = len(desired)
        print('Found ' + str(found) + ' servers')
        if found == 0:
            exit(1)
        winner = sorted(desired, key=lambda s: float(s['Score'].replace(',', '.')), reverse=True)[0]
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
    keys = ['#HostName', 'IP', 'Score', 'Ping']
    filtered = dict(winner)
    del filtered['OpenVPN_ConfigData_Base64']
    for (l, d) in filtered.items():
        if l == 'Speed':
            print('Speed: {0} MBps'.format(round(int(winner['Speed']) / 10 ** 6), 2))
        else:
            print(l + ': ' + d)
    # print("Country: " + winner['CountryLong'])

    print("\nLaunching VPN...")
    path = get_tblk_path()
    usefake = False
    if not path or not os.path.exists(path):
        print("Please add first OpenVpn connection by hand, name it 'VPNGate' you can use VPNGate.ovpn from you desktop as example")
        path = os.path.expanduser("~/Desktop/VPNGate.ovpn")
        usefake = True
        # exit(-1)
    else:
        path = os.path.join(path, "Contents/Resources/config.ovpn")
    f = open(path, 'wb')
    f.write(base64.b64decode(winner['OpenVPN_ConfigData_Base64']))
    f.close()
    if not usefake:
        x = subprocess.call(['osascript', 'script.scpt'])
        print(x)


def get_tblk_path():
    for dir in CONFIG_DIRS:
        dir = os.path.join(os.path.expanduser(dir), "VPNGate.tblk")
        if os.path.exists(dir) and os.path.isdir(dir):
            return dir


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
