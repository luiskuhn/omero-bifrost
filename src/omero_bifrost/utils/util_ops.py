
def get_omero_config(config_file_path, server_profile="OmeroServerSection"):

    import configparser

    config = configparser.RawConfigParser()
    config.read(config_file_path)

    profile = server_profile.strip() if isinstance(server_profile, str) else "OmeroServerSection"
    if profile == "":
        profile = "OmeroServerSection"

    if not config.has_section(profile):
        raise ValueError(
            "Unknown OMERO server profile '" + str(profile) + "' in config file '" + str(config_file_path) + "'."
        )

    omero_username = config.get(profile, 'omero.username')
    omero_password = config.get(profile, 'omero.password')
    omero_host = config.get(profile, 'omero.host')
    omero_port = int(config.get(profile, 'omero.port'))

    # optional user group context (kept backward compatible)
    omero_group = None
    if config.has_option(profile, 'omero.group'):
        group_value = config.get(profile, 'omero.group').strip()
        if group_value != "":
            omero_group = group_value

    return omero_username, omero_password, omero_host, omero_port, omero_group

def format_xml_ouput(output_map):

    import xml.etree.ElementTree as ET

    output_root_element = ET.Element('omero-bifrost-output')
    for key in output_map.keys():
        output_element = ET.SubElement(output_root_element, "output-item")
        output_element.attrib = {"index":str(key),
                                 "type":output_map[key]["type"],
                                 "name":output_map[key]["name"],
                                 "id":output_map[key]["id"]}

    output_root_element.attrib = {"size":str(len(output_map.keys()))}
    xml_tree = ET.ElementTree(output_root_element)

    return xml_tree

def omero_connect(usr, pwd, host, port, group=None):
    """
    Connects to the OMERO Server with the provided username and password.

    Args:
        usr: The username to log into OMERO
        pwd: a password associated with the given username
        host: the OMERO hostname
        port: the port at which the OMERO server can be reached

    Returns:
        Connected BlitzGateway to the OMERO Server with the provided credentials

    """
    from omero.gateway import BlitzGateway

    conn = BlitzGateway(usr, pwd, host=host, port=port)
    connected = conn.connect()
    conn.setSecure(True)

    if not connected:
        print("Error: Connection not available")
        return conn

    if group is not None:
        try:
            if isinstance(group, str) and group.isdigit():
                conn.SERVICE_OPTS.setOmeroGroup(int(group))
            else:
                target_groups = list(conn.getObjects("ExperimenterGroup", attributes={"name": str(group)}))
                if len(target_groups) > 0:
                    conn.SERVICE_OPTS.setOmeroGroup(target_groups[0].getId())
                else:
                    print("Warning: OMERO group not found: " + str(group))
        except Exception as exc:
            print("Warning: Failed to set OMERO group context: " + str(exc))

    return conn

def img_map_from_tsv(tsv_file_path):
    import csv

    img_map = {}

    line_list = []
    with open(tsv_file_path) as file:
        tsv_file = csv.reader(file, delimiter="\t")
        for line in tsv_file:
            line_list.append(line)

    if line_list[0][0] == "OMERO_IMG_ID":
        del line_list[0]
        for line in line_list:
            try:
                img_id = int(line[0])
                if len(line) >= 3:
                    img_map[img_id] = [line[1], line[2]]
                else:
                    img_map[img_id] = ["null", "null"]
            except ValueError:
                print("Error parsing image id list: string not int value")
    else:
        print("Error parsing image id list: wrong header text")


    return img_map
