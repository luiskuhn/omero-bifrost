
from dataclasses import dataclass


@dataclass
class OmeroGroupResolution:
    requested_group: str | None
    resolved_group_id: int | None
    resolved_group_name: str | None
    strict: bool
    status: str


class OmeroGroupResolutionError(ValueError):
    pass


def get_omero_config(config_file_path, server_profile="default"):

    import configparser

    config = configparser.RawConfigParser()
    config.read(config_file_path)

    required_keys = ('omero.username', 'omero.password', 'omero.host', 'omero.port', 'omero.group')
    profile_section_prefix = 'OmeroServer:'

    def _clean(value):
        return value.strip() if isinstance(value, str) else value

    requested_profile = str(server_profile).strip()
    section_name = profile_section_prefix + requested_profile

    if not config.has_section(section_name):
        available = sorted([s.split(':', 1)[1] for s in config.sections() if s.startswith(profile_section_prefix)])
        raise ValueError(
            "Unknown OMERO server profile '{0}'. Expected section '[{1}]'. Available profiles: {2}.".format(
                requested_profile, section_name, ", ".join(available) if available else "none"
            )
        )

    selected_values = {}
    missing = []
    for key in required_keys:
        if config.has_option(section_name, key) and _clean(config.get(section_name, key)) != '':
            selected_values[key] = _clean(config.get(section_name, key))
        else:
            missing.append(key)

    if missing:
        raise ValueError(
            "Profile '{0}' is missing required OMERO keys in section '[{1}]': {2}".format(
                requested_profile, section_name, ", ".join(missing)
            )
        )

    try:
        port = int(selected_values['omero.port'])
    except Exception:
        raise ValueError(f"Invalid OMERO port for profile '{requested_profile}': {selected_values.get('omero.port')}")

    return (
        selected_values['omero.username'],
        selected_values['omero.password'],
        selected_values['omero.host'],
        port,
        selected_values['omero.group'],
    )


def _resolve_group_context(conn, group):
    if group is None:
        return OmeroGroupResolution(None, None, None, True, 'not-requested')
    if isinstance(group, str) and group.isdigit():
        gid = int(group)
        groups = list(conn.getObjects("ExperimenterGroup", attributes={"id": gid}))
        name = groups[0].getName() if groups else None
        return OmeroGroupResolution(str(group), gid, name, True, 'resolved-by-id' if groups else 'id-not-visible')
    groups = list(conn.getObjects("ExperimenterGroup", attributes={"name": str(group)}))
    if groups:
        g = groups[0]
        return OmeroGroupResolution(str(group), int(g.getId()), g.getName(), True, 'resolved-by-name')
    return OmeroGroupResolution(str(group), None, None, True, 'name-not-found')


def omero_connect(usr, pwd, host, port, group=None, strict_group_scope=True):
    """Create OMERO connection with strict group resolution.

    If ``group`` is provided and cannot be resolved by visible ID or name,
    ``OmeroGroupResolutionError`` is raised. No lenient fallback behavior is applied.
    """
    from omero.gateway import BlitzGateway

    conn = BlitzGateway(usr, pwd, host=host, port=port)
    connected = conn.connect()
    conn.setSecure(True)

    if not connected:
        print("Error: Connection not available")
        return conn

    group_ctx = _resolve_group_context(conn, group)
    conn.bifrost_group_context = group_ctx
    if group is not None:
        if group_ctx.resolved_group_id is None:
            msg = f"Unable to access OMERO group '{group}' ({group_ctx.status})"
            raise OmeroGroupResolutionError(msg)
        conn.SERVICE_OPTS.setOmeroGroup(group_ctx.resolved_group_id)

    return conn

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
