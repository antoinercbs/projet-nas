import yaml

def invert_ip(ip):
    new_ip = ""
    for n in ip.split('.'):
        new_ip += str(255-int(n))
        new_ip += '.'
    return new_ip[:-1]

def apply_mask(ip, mask):
    ma = mask.split('.')
    n = ip.split('.')
    new_ip = ""
    for i in range(4):
        new_ip += str(int(ma[i]) & int(n[i]))
        new_ip += '.'
    return new_ip[:-1]


def configure_backbone_ospf(conf, ospf_conf):
    mpls = ospf_conf["use-mpls"]
    ospf_lo = ospf_conf["ospf-on-loopback"]
    for r_ospf in ospf_conf["routers"]:
        for r_conf in conf["routers"]:
            if r_ospf["name"] == r_conf["global"]["hostname"]:
                r_conf["ospf"] = []
                process_conf = dict()
                process_conf["process-number"] = "1"
                process_conf["networks"] = []
                if ospf_lo:
                    for lo in r_conf["loopbacks"]:
                        if lo["number"] == 0:
                            sub_conf = dict()
                            sub_conf["subnet"] = lo["address"]
                            sub_conf["mask"] = invert_ip(lo["mask"])
                            sub_conf["area"] = "0"
                            process_conf["networks"].append(sub_conf)
                for int_conf in r_conf["interfaces"]:
                    for nei in r_ospf["backbone-neighbors"]:
                        if nei["interface"] == int_conf["name"]:
                            if mpls:
                                int_conf["mpls-ip"] = True
                            sub_conf = dict()
                            sub_conf["subnet"] = apply_mask(int_conf["address"], int_conf["mask"])
                            sub_conf["mask"] = invert_ip(int_conf["mask"])
                            sub_conf["area"] = "0"
                            process_conf["networks"].append(sub_conf)
                r_conf["ospf"].append(process_conf)

def configure_internal_bgp(conf, bgp_conf):
    vpn = bgp_conf["activate-vpn"]
    for router in conf["routers"]: 
        for bgp_pe in bgp_conf["edge-routers"]:
            if router["global"]["hostname"] == bgp_pe["name"]:
                router["bgp"] = dict()
                router["bgp"]["as-number"] = bgp_conf["as-number"]
                router["bgp"]["address-families"] = []
                if vpn:
                    fam_conf = dict()
                    fam_conf["family"] = "vpnv4"
                    fam_conf["neighbors"] = []
                router["bgp"]["neighbors"] = []
                for nei_bgp_pe in bgp_conf["edge-routers"]: 
                    if router["global"]["hostname"] != nei_bgp_pe["name"]:
                        for nei_router in conf["routers"]: 
                            if nei_router["global"]["hostname"] == nei_bgp_pe["name"]:
                                nei_conf = dict()
                                nei_conf["address"] = nei_router["loopbacks"][0]["address"]
                                nei_conf["remote-as"] = bgp_conf["as-number"]
                                nei_conf["update-source"] = "lo0"
                                router["bgp"]["neighbors"].append(nei_conf)
                                if vpn:
                                    fam_nei_conf = dict()
                                    fam_nei_conf["address"] = nei_conf["address"]
                                    fam_nei_conf["activate"] = True
                                    fam_conf["neighbors"].append(fam_nei_conf)
                router["bgp"]["address-families"].append(fam_conf)

def configure_vrf(conf, network_conf):
    vpn_conf = network_conf["vpn"]
    rd = 1
    for vpn in vpn_conf:
        for site in vpn["sites"]:
            for router in conf["routers"]:
                if router["global"]["hostname"] == site["pe-router"]["name"]:
                    if not ("vrf" in router.keys()):
                        router["vrf"] = []
                    vrf_conf = dict()
                    vrf_conf["name"] = vpn["vrf-name"]
                    vrf_conf["rd"] = rd
                    vrf_conf["as_number"] = network_conf["ibgp"]["as-number"]
                    router["vrf"].append(vrf_conf)
        rd += 1

def configure_ce_bgp(conf, network_conf):
    vpn_conf = network_conf["vpn"]
    for vpn in vpn_conf:
        for site in vpn["sites"]:
            for router in conf["routers"]:
                if router["global"]["hostname"] == site["ce-router"]["name"]:
                    router["bgp"] = dict()
                    router["bgp"]["as-number"] = site["ce-router"]["as-number"]
                    router["bgp"]["networks"] = []
                    router["bgp"]["neighbors"] = []
                    for inter in site["ce-router"]["interfaces-to-local"]:
                        for inter_conf in router["interfaces"]:
                            if inter["name"] == inter_conf["name"]:
                                net_conf = dict()
                                net_conf["address"] = apply_mask(inter_conf["address"], inter_conf["mask"])
                                net_conf["mask"] = inter_conf["mask"]
                                router["bgp"]["networks"].append(net_conf)
                    for pe_router in conf["routers"]:
                        if pe_router["global"]["hostname"] == site["pe-router"]["name"]:
                            nei_conf = dict()
                            nei_conf["remote-as"] = network_conf["ibgp"]["as-number"]
                            for pe_inter in pe_router["interfaces"]:
                                if pe_inter["name"] == site["pe-router"]["interface-to-ce"]:
                                    nei_conf["address"] = pe_inter["address"]
                            router["bgp"]["neighbors"].append(nei_conf)

def configure_ce_ospf(conf, network_conf):
    vpn_conf = network_conf["vpn"]
    for vpn in vpn_conf:
        for site in vpn["sites"]:
            for router in conf["routers"]:
                if router["global"]["hostname"] == site["ce-router"]["name"]:
                    router["ospf"] = []
                    ospf_conf = dict()
                    ospf_conf["process-number"] = "1"
                    ospf_conf["networks"] = []
                    for inter in site["ce-router"]["interfaces-to-local"]:
                        for inter_conf in router["interfaces"]:
                            if inter["name"] == inter_conf["name"]:
                                net_conf = dict()
                                net_conf["area"] = "0"
                                net_conf["address"] = apply_mask(inter_conf["address"], inter_conf["mask"])
                                net_conf["mask"] = invert_ip(inter_conf["mask"])
                                ospf_conf["networks"].append(net_conf)
                    for inter_conf in router["interfaces"]:
                        if site["ce-router"]["interface-to-pe"] == inter_conf["name"]:
                            net_conf = dict()
                            net_conf["area"] = "0"
                            net_conf["address"] = apply_mask(inter_conf["address"], inter_conf["mask"])
                            net_conf["mask"] = invert_ip(inter_conf["mask"])
                            ospf_conf["networks"].append(net_conf)
                    router["ospf"].append(ospf_conf)

def configure_pe_bgp(conf, network_conf):
    vpn_conf = network_conf["vpn"]
    for router in conf["routers"]:
        for vpn in vpn_conf:
            for site in vpn["sites"]:
                if router["global"]["hostname"] == site["pe-router"]["name"]:
                    for ce_router in conf["routers"]:
                        if ce_router["global"]["hostname"] == site["ce-router"]["name"]:
                            af_conf= dict()
                            af_conf["family"] = "ipv4"
                            af_conf["vrf"] = vpn["vrf-name"]
                            af_conf["neighbors"] = []
                            for ce_inter_conf in ce_router["interfaces"]:
                                if site["ce-router"]["interface-to-pe"] == ce_inter_conf["name"]:
                                    net_conf = dict()
                                    net_conf["address"] = ce_inter_conf["address"]
                                    net_conf["remote-as"] = site["ce-router"]["as-number"]
                                    af_conf["neighbors"].append(net_conf)
                            router["bgp"]["address-families"].append(af_conf)













if __name__ == "__main__":
    with open('network_config.yaml') as network_conf_file:
        with open('startup_config.yaml') as startup_conf_file:
            network_conf = yaml.full_load(network_conf_file)
            conf = yaml.full_load(startup_conf_file)

            configure_backbone_ospf(conf, network_conf["backbone-ospf"])
            configure_internal_bgp(conf, network_conf["ibgp"])
            configure_vrf(conf, network_conf)
            configure_ce_bgp(conf, network_conf)
            configure_ce_ospf(conf, network_conf)
            configure_pe_bgp(conf, network_conf)

            with open('output.yaml', 'w') as output_file:
                documents = yaml.dump(conf, output_file)
            

