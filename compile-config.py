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




if __name__ == "__main__":
    with open('network_config.yaml') as network_conf_file:
        with open('startup_config.yaml') as startup_conf_file:
            ospf_conf = yaml.full_load(network_conf_file)
            conf = yaml.full_load(startup_conf_file)
            configure_backbone_ospf(conf, ospf_conf["backbone-ospf"])
            with open('output.yaml', 'w') as output_file:
                documents = yaml.dump(conf, output_file)
            

