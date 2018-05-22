#!/usr/bin/env python

"""Pick server and start connection with VPNGate (http://www.vpngate.net/en/)"""
import datetime
import errno

import requests, os, sys, tempfile, subprocess, base64, time

CACHE_PATH = 'vpngate.txt'

if len(sys.argv) == 2:
#     print('usage: ' + sys.argv[0] + ' [country name | country code]')
#     exit(1)
    country = sys.argv[1]
else:
    country = ''

if len(country) == 2:
    i = 6 # short name for country
elif len(country) > 2:
    i = 5 # long name for country
else:
    i = 0
#     print('Country is too short!')
#     exit(1)


def get_vpn_data():
    delta = sys.maxsize
    if os.path.exists(CACHE_PATH):
        filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_PATH))
        today = datetime.datetime.today()
        delta = today - filemtime
    if delta > datetime.timedelta(days=1):
        with open(CACHE_PATH, 'w') as f:
            f.write(requests.get('http://www.vpngate.net/api/iphone/').text.replace('\r', ''))
    with open(CACHE_PATH, 'r') as f:
        return f.read()


try:
    vpn_data = get_vpn_data()
    servers = [line.split(',') for line in vpn_data.split('\n')]
    labels = servers[1]
    labels[0] = labels[0][1:]
    servers = [s for s in servers[2:] if len(s) > 1]
except:
    print('Cannot get VPN servers data')
    exit(1)

if i > 0:
    desired = [s for s in servers if country.lower() in s[i].lower()]
else:
    desired = servers
found = len(desired)
print('Found ' + str(found) + ' servers for country ' + country)
if found == 0:
    exit(1)

supported = [s for s in desired if len(s[-1]) > 0]
print(str(len(supported)) + ' of these servers support OpenVPN')
# We pick the best servers by score
winner = sorted(supported, key=lambda s: float(s[2].replace(',','.')), reverse=True)[0]

print("\n== Best server ==")
pairs = list(zip(labels, winner))[:-1]
for (l, d) in pairs[:4]:
    print(l + ': ' + d)

print(pairs[4][0] + ': ' + str(float(pairs[4][1]) / 10**6) + ' MBps')
print("Country: " + pairs[5][1])

print("\nLaunching VPN...")
_, path = tempfile.mkstemp()
# import os
path = os.path.expanduser("~/Library/Application Support/Tunnelblick/Configurations/VPNGate.tblk/Contents/Resources/config.ovpn")
# path = os.path.expanduser("~/VpnGate.tblk/Contents/Resources/config.ovpn")
if not os.path.exists(path):
    print("Please add first OpenVpn connection by hand, name it 'VPNGate'")
    exit(-1);
    # try:
    #     os.makedirs(os.path.dirname(path))
    # except OSError as exc: # Guard against race condition
    #     if exc.errno != errno.EEXIST:
    #         raise
f = open(path, 'wb')
f.write(base64.b64decode(winner[-1]))
# f.write('\nscript-security 2\nup /etc/openvpn/update-resolv-conf\ndown /etc/openvpn/update-resolv-conf')
f.close()
scripts = ["tell application \"Tunnelblick\"", "disconnect \"VPNGate\"", "connect \"VPNGate\"", "end tell"]
args = ['osascript']
for i, a in enumerate(scripts):
    args = args + ['-e', a]

x = subprocess.call(args)
time.sleep(2)

# try:
#     while True:
#         time.sleep(600)
# termination with Ctrl+C
# except:
#     try:
#         x.kill()
#     except:
#         pass
#     while x.poll() != 0:
#         time.sleep(1)
#     print('\nVPN terminated')