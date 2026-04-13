
def get_omero_config(config_file_path, server_profile="OmeroServerSection"):

    import configparser

    config = configparser.RawConfigParser()
    config.read(config_file_path)

    required_keys = ('omero.username', 'omero.password', 'omero.host', 'omero.port')
    optional_group_key = 'omero.group'
    legacy_section = 'OmeroServerSection'
    profile_section_prefix = 'OmeroServer:'

    def _clean_value(value):
        return value.strip() if isinstance(value, str) else value

    def _existing_profile_sections():
        profiles = []
        for section_name in config.sections():
            if section_name.startswith(profile_section_prefix):
                profiles.append(section_name.split(':', 1)[1])
        return sorted(profiles)

    def _existing_prefixed_profiles():
        profiles = set()
        all_options = set(config.defaults().keys())
        if config.has_section(legacy_section):
            all_options.update(config.options(legacy_section))
        for option_name in all_options:
            if option_name.endswith('.omero.username') and '.' in option_name:
                profiles.add(option_name.rsplit('.omero.username', 1)[0])
        return sorted(profiles)

    # 1) Explicit named section: [OmeroServer:<profile>]
    selected_section = None
    if profile is not None:
        profile_section = profile_section_prefix + str(profile)
        if config.has_section(profile_section):
            selected_section = profile_section
    else:
        legacy_present = config.has_section(legacy_section)
        discovered_profiles = _existing_profile_sections()
        if legacy_present:
            selected_section = legacy_section
        elif len(discovered_profiles) == 1:
            selected_section = profile_section_prefix + discovered_profiles[0]
        elif len(discovered_profiles) > 1:
            raise ValueError(
                "Multiple OMERO profiles found in config ({0}). "
                "Please provide a profile name.".format(", ".join(discovered_profiles))
            )

    selected_values = {}
    missing_required = []

    if selected_section is not None:
        for key in required_keys:
            if config.has_option(selected_section, key):
                selected_values[key] = _clean_value(config.get(selected_section, key))
            else:
                missing_required.append(key)
        if config.has_option(selected_section, optional_group_key):
            selected_values[optional_group_key] = _clean_value(config.get(selected_section, optional_group_key))
    else:
        # 2) Default/legacy section using profile-prefixed keys, e.g.:
        #    eu.omero.username, us.omero.host, ...
        key_prefix = ""
        if profile is not None:
            key_prefix = str(profile).strip() + "."

        def _lookup_prefixed_option(option_name):
            if config.has_section(legacy_section) and config.has_option(legacy_section, option_name):
                return _clean_value(config.get(legacy_section, option_name))
            if option_name in config.defaults():
                return _clean_value(config.defaults()[option_name])
            return None

        for key in required_keys:
            lookup_key = key_prefix + key
            value = _lookup_prefixed_option(lookup_key)
            if value in (None, ""):
                missing_required.append(lookup_key)
            else:
                selected_values[key] = value

        group_lookup_key = key_prefix + optional_group_key
        group_value = _lookup_prefixed_option(group_lookup_key)
        if group_value not in (None, ""):
            selected_values[optional_group_key] = group_value

    if missing_required:
        if profile is None:
            raise ValueError(
                "Missing required OMERO config keys: {0}. "
                "Use [OmeroServerSection], a single [OmeroServer:<profile>] section, "
                "or provide a profile for multi-profile configs.".format(", ".join(missing_required))
            )

        available_profiles = sorted(set(_existing_profile_sections() + _existing_prefixed_profiles()))
        available_profile_text = ", ".join(available_profiles) if available_profiles else "none"
        raise ValueError(
            "Profile '{0}' is missing required OMERO keys: {1}. "
            "Available profiles: {2}.".format(profile, ", ".join(missing_required), available_profile_text)
        )

    omero_username = selected_values['omero.username']
    omero_password = selected_values['omero.password']
    omero_host = selected_values['omero.host']
    try:
        omero_port = int(selected_values['omero.port'])
    except (TypeError, ValueError):
        profile_label = "default" if profile is None else str(profile)
        raise ValueError("Invalid OMERO port for profile '{0}': {1}".format(profile_label, selected_values['omero.port']))

    # optional user group context (kept backward compatible)
    omero_group = None
    if optional_group_key in selected_values:
        group_value = selected_values[optional_group_key]
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
