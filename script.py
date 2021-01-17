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
    enable_password = global_conf["enable-password"]
    tn.write(user.encode('ascii') + b"\n")
    tn.read_until(b"Password: ")
    tn.write(password.encode('ascii') + b"\n")
    tn.write(b"enable\n")
    tn.write(enable_password.encode('ascii') + b"\n")
    
    return tn

def configure_interface(tn, interface_conf):
    tn.write(b"conf t\n")
    name = interface_conf["name"]
    tn.write(b"int " + name.encode('ascii') + b"\n")
    address = interface_conf["address"]
    mask = ""
    if ("mask" in interface_conf.keys()):
        mask = interface_conf["mask"]
    tn.write(b"ip address " + address.encode('ascii') + b" " + mask.encode('ascii') + b"\n")
    if (interface_conf["no-shutdown"]):
        tn.write(b"no shutdown\n")
    tn.write(b"end\n")


if __name__ == "__main__":
    with open('config.yaml') as cf:
        conf_file = yaml.full_load(cf)
        for conf in conf_file["routers"]:
            print("Configuration of", conf["global"]["hostname"])
            tn = connect_to_host(conf["global"])
            for int_conf in conf["interfaces"]:
                configure_interface(tn, int_conf)
            tn.write(b"exit\n")
            print(tn.read_all().decode('ascii'))





