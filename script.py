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

def configure_loopback(tn, interface_conf):
    tn.write(b"conf t\n")
    number = str(interface_conf["number"])
    tn.write(b"int loopback " + number.encode('ascii') + b"\n")
    address = interface_conf["address"]
    mask = interface_conf["mask"]
    tn.write(b"ip address " + address.encode('ascii') + b" " + mask.encode('ascii') + b"\n")
    tn.write(b"end\n")

def remove_loopback(tn, num):
    tn.write(b"conf t\n")
    number = str(num)
    tn.write(b"no int loopback " + number.encode('ascii') + b"\n")
    tn.write(b"end\n")


def configure_dhcp(tn, conf):
    tn.write(b"conf t\n")
    max_add = conf["excluded-address-max"]
    min_add = conf["excluded-address-min"]
    pool_name = conf["pool-name"]
    subnet = conf["subnet"]
    mask = conf["subnet-mask"]
    def_router = conf["default-router"]
    dns_serv = conf["dns-server"]

    tn.write(b"ip dhcp excluded-address " + min_add.encode('ascii') + b" " + max_add.encode('ascii') + b"\n")
    tn.write(b"ip dhcp pool " + pool_name.encode('ascii') + b"\n")
    tn.write(b"network " + subnet.encode('ascii') + b" " + mask.encode('ascii') + b"\n")
    tn.write(b"default-router " + def_router.encode('ascii') + b"\n")
    tn.write(b"dns-server " + dns_serv.encode('ascii') + b"\n")
    tn.write(b"end\n")





if __name__ == "__main__":
    with open('config.yaml') as cf:
        conf_file = yaml.full_load(cf)

        for conf in conf_file["routers"]:
            print("Configuration of", conf["global"]["hostname"])
            tn = connect_to_host(conf["global"])
            
            if ("loopbacks" in conf.keys()):
                defined = [False for i in range(0, 10)]
                for loopback_conf in conf["loopbacks"]:
                    defined[loopback_conf["number"]] = True
                    configure_loopback(tn, loopback_conf)
                for i in range(len(defined)):
                    if not defined[i]:
                        remove_loopback(tn, i)

            for int_conf in conf["interfaces"]:
                configure_interface(tn, int_conf)

            if ("dhcp" in conf.keys()):
                configure_dhcp(tn, conf["dhcp"])

            tn.write(b"exit\n")
            print(tn.read_all().decode('ascii'))





