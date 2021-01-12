#!/usr/bin/env python

# SQL database logins
sql_dict = {
    "home": "dbname='system_check' user='system_check' host='localhost' password='syscheck'"
}

# Dictionaries for various system IDs
windows_tablet_dict = {
    'PID_00B1': 'Intuos3 6x18',
    'PID_00B2': 'Intuos3 9x12',
    'PID_00B5': 'Intuos3 6x11',
    'PID_00B9': 'Intuos4 6x9',
    'PID_00BA': 'Intuos4 8x13',
    'PID_0357': 'Intuos Pro 2 M',
    'PID_0315': 'Intuos Pro M',
}
linux_tablet_dict = {
    '00B1': 'Intuos3 6x18',
    '00B2': 'Intuos3 9x12',
    '00B5': 'Intuos3 6x11',
    '00B9': 'Intuos4 6x9',
    '00BA': 'Intuos4 8x13',
    '0357': 'Intuos Pro 2 M',
    '0315': 'Intuos Pro M',
}

# GPU microarchitectures - pattern matches names and assigns their respective archs.
gpu_arch_dict = {
    'Quadro RTX [0-9]*': 'turing',
    'Quadro GV[0-9]*': 'volta',
    'Quadro GP[0-9]*': 'pascal',
    'Quadro P[0-9]{4}': 'pascal',
    'TITAN Xp': 'pascal',
    'GTX 10[0-9]{2}': 'pascal',
    'Quadro M[0-9]{4}': 'maxwell',
    'GTX TITAN X': 'maxwell',
    'GTX 9[0-9]{2}': 'maxwell',
    'Quadro K[0-9]{4}': 'kepler',
    'GTX TITAN Black': 'kepler',
    'GTX [6-7][0-9]{2}': 'kepler',
    'Quadro [0-9]{4}': 'fermi',
    'GTX [5][0-9]{2}': 'fermi',
    'Quadro FX [3-9][0-9]{3}': 'tesla',
    'Quadro FX 770M': 'tesla',
    'Quadro FX 1500': 'curie',
    'Tesla V[0-9]{3}': 'volta',
    'Quadro RTX A[0-9]{4}': 'ampere',
    'GeForce RTX 20[0-9]{2}': 'turing',
}
