#!/usr/bin/env python3

# Procedure préalable sur routeur :
# en
# conf t
# host <nom routeur>
# enable password cisco
# username antoine password cisco
# line vty 0 4
# login local 
# transport input all
# int <interface e.g. g1/0>
# ip address dhcp 
# no shut
# end 
# sh ip int brief


import getpass
import telnetlib
import yaml

def connect_to_host(global_conf):
    tn = telnetlib.Telnet(global_conf["host"])
    tn.read_until(b"Username: ")
    user = global_conf["username"]
    password = global_conf["password"]
    tn.write(user.encode('ascii') + b"\n")
    tn.read_until(b"Password: ")
    tn.write(password.encode('ascii') + b"\n")
    
    return tn



if __name__ == "__main__":
    with open('config.yaml') as cf:
        conf = yaml.full_load(cf)
        tn = connect_to_host(conf["global"])
        tn.write(b"exit\n")
        print(tn.read_all().decode('ascii'))



"""tn.write(b"enable\n")
tn.write(b"cisco\n")
tn.write(b"conf t\n")
tn.write(b"int loop 0\n")
tn.write(b"ip address 1.1.1.1 255.255.255.255\n")
tn.write(b"end\n")
"""



