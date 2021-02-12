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
# copy running-config startup-config


import telnetlib
import yaml
import time


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

def configure_ospf(tn, conf):
    tn.write(b"conf t\n")
    num = conf["process-number"]
    if ("vrf" in conf.keys()):
        vrf = conf["vrf"]
        tn.write(b"no router ospf " + num.encode('ascii') + b" vrf "+ vrf.encode('ascii') +b"\n")
        tn.write(b"router ospf " + num.encode('ascii') + b" vrf "+ vrf.encode('ascii') + b"\n")
    else:
        tn.write(b"no router ospf " + num.encode('ascii') + b"\n")
        tn.write(b"router ospf " + num.encode('ascii') + b"\n")
    if ("redistribute-bgp-subnets" in conf.keys()):
        tn.write(b"redistribute bgp " + conf["redistribute-bgp-subnets"].encode('ascii') + b" subnets" + b"\n")
    for net in conf["networks"]:
        tn.write(b"network " + net["subnet"].encode('ascii') + b" " + net["mask"].encode('ascii') + b" area " + net["area"].encode('ascii') + b"\n")
    tn.write(b"end\n")

def configure_vrf(tn, conf):
    for vrf in conf:
        tn.write(b"conf t\n")
        name = vrf["name"].encode('ascii')
        #tn.write(b"no ip vrf " + name + b"\n")
        tn.write(b"ip vrf " + name + b"\n")
        if ("rd" in vrf.keys()):
            as_number = vrf["as-number"].encode('ascii')
            rd = vrf["rd"].encode('ascii')
            tn.write(b"rd " + as_number + b":" + rd + b"\n")
            tn.write(b"route-target both " + as_number + b":" + rd + b"\n")
        tn.write(b"end\n")
    

def configure_bgp(tn, conf):
    as_number = conf["as-number"].encode('ascii')
    tn.write(b"conf t\n")
    tn.write(b"no router bgp "+ as_number +b"\n")
    tn.write(b"router bgp "+ as_number +b"\n")
    if ("neighbors" in conf.keys()):
        for nei in conf["neighbors"]:
            nei_add = nei["address"].encode('ascii')
            if ("remote-as" in nei.keys()):
                tn.write(b"neighbor " + nei_add + b" remote-as " + nei["remote-as"].encode('ascii') + b"\n")
            if ("update-source" in nei.keys()):
                tn.write(b"neighbor " + nei_add + b" update-source " + nei["update-source"].encode('ascii') + b"\n")
    if ("address-families" in conf.keys()):
        for af in conf["address-families"]:
            if ("vrf" in af.keys()):
                vrf = af["vrf"].encode('ascii')
                tn.write(b"address-family " + af["family"].encode('ascii') + b" vrf "+ vrf +b"\n")
            else:
                tn.write(b"address-family " + af["family"].encode('ascii') + b"\n")
            if ("neighbors" in af.keys()):
                for nei in af["neighbors"]:
                    nei_add = nei["address"].encode('ascii')
                    if ("activate" in nei.keys()):
                        if (nei["activate"]):
                            tn.write(b"neighbor " + nei_add + b" activate\n")
                    if ("remote-as" in nei.keys()):
                        tn.write(b"neighbor " + nei_add + b" remote-as "+ nei["remote-as"].encode('ascii') + b"\n")
            tn.write(b"exit\n")
    if ("networks" in conf.keys()):
        for net in conf["networks"]:
            subnet = net["address"].encode('ascii')
            mask = net["mask"].encode('ascii')
            tn.write(b"network " + subnet + b" mask "+ mask + b"\n")
    tn.write(b"end\n")


def configure_interface(tn, interface_conf):
    tn.write(b"conf t\n")
    name = interface_conf["name"]
    tn.write(b"int " + name.encode('ascii') + b"\n")
    address = interface_conf["address"]
    mask = ""
    if ("vrf-forwarding" in interface_conf.keys()):
        vrf = interface_conf["vrf-forwarding"].encode('ascii')
        tn.write(b"ip vrf forwarding " + vrf + b"\n")
    if ("mask" in interface_conf.keys()):
        mask = interface_conf["mask"]
    tn.write(b"ip address " + address.encode('ascii') + b" " + mask.encode('ascii') + b"\n")
    if ("mpls-ip" in interface_conf.keys()):
        if (interface_conf["mpls-ip"]):
            tn.write(b"mpls ip\n")
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
            
            if ("vrf" in conf.keys()):
                configure_vrf(tn, conf["vrf"])

            if ("loopbacks" in conf.keys()):
                for loopback_conf in conf["loopbacks"]:
                    configure_loopback(tn, loopback_conf)

            if ("interfaces" in conf.keys()):
                for int_conf in conf["interfaces"]:
                    configure_interface(tn, int_conf)

            if ("dhcp" in conf.keys()):
                configure_dhcp(tn, conf["dhcp"])

            if ("ospf" in conf.keys()):
                for ospf_conf in conf["ospf"]:
                    configure_ospf(tn, ospf_conf)

            if ("bgp" in conf.keys()):
                configure_bgp(tn, conf["bgp"])

            tn.write(b"exit\n")
            print(tn.read_all().decode('ascii'))





