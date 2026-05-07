"""Typer CLI entrypoints for OMERO-Bifrost query, push, and pull commands."""


"""Workflow-first interface to OMERO image and metadata operations.

This CLI is designed to support automated execution in Nextflow and nf-core
pipelines, while still being usable as a regular command line tool. It
provides commands to query, push, and pull image data and FAIR-oriented
metadata across OMERO servers.

Current capabilities include:
    * programmatic query of projects, datasets, and image IDs
    * metadata-based image filtering (key-values and tags)
    * image import/export and original file download
    * metadata and annotation write operations

Configuration supports credentials and an optional user group context for
OMERO session scoping. This is a building block towards a multi-server
"constellation" design where multiple OMERO endpoints are orchestrated from
workflow code.
"""

import typer
from rich import print
from typing import Annotated, List

from omero_bifrost.utils.filter_expr import FilterParseError, parse_filter_exprs

#####################################

from omero_bifrost.utils.util_ops import get_omero_config, omero_connect, img_map_from_tsv
from omero_bifrost.query.query_ops import fetch_all_objects, get_omero_dataset_id
from omero_bifrost.push.push_ops import register_image_file_with_dataset_id, register_image_folder_with_dataset_id 
from omero_bifrost.push.push_ops import attach_file_to_image, create_tag, add_tag_to_image, add_kv_to_image
from omero_bifrost.pull.pull_ops import download_original_image_file, export_ome_tiff_file, export_ome_xml_file
from omero_bifrost.utils.omero_cli_runner import OmeroCliError
from omero_bifrost.utils.output_ops import serialize_execution_output

#####################################

app = typer.Typer()

query_app = typer.Typer()
push_app = typer.Typer()
pull_app = typer.Typer()
app.add_typer(query_app, name="query", help="Query an OMERO server for Project, Dataset, and Image objects.")
app.add_typer(push_app, name="push", help="Push image data into an OMERO Server.")
app.add_typer(pull_app, name="pull", help="Pull image data from an OMERO Server.")



def _handle_cli_error(exc: Exception, *, code: int = 2):
    print(f"[bold red]ERROR|{exc.__class__.__name__}|{exc}")
    raise typer.Exit(code=code)


CONFIG_HELP_TEXT = (
    "Path to OMERO config properties file. Used together with --server-profile to select credentials."
)
SERVER_PROFILE_HELP_TEXT = (
    "Config section/profile name loaded from --config section [OmeroServer:<profile>] (default: default)."
)


def _emit_execution_output(records, *, profile: str, to_file: bool = False, to_console: bool = False, output_file_path: str = "", provenance: dict | None = None):
    payload = {
        "provenance": provenance or {"tool": "omero-bifrost-cli"},
        "profiles": {profile: {"status": "ok", "count": len(records)}},
        "records": records,
    }
    serialized = serialize_execution_output(payload)
    if to_file:
        with open(output_file_path, "w", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
    else:
        print(serialized)


def _load_omero_config(config_file_path: str, server_profile: str):
    try:
        return get_omero_config(config_file_path, server_profile=server_profile)
    except ValueError as exc:
        _handle_cli_error(exc)


@query_app.command("list-all", help="Query all accessible OMERO objects")
def query_list_all(
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    objects = fetch_all_objects(conn)
    records = [{"index": key, **value} for key, value in objects.items()]
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

    conn.close()


@query_app.command("dataset-id", help="Query the ID of an OMERO dataset using project and dataset names")
def query_dataset_id(
        project: Annotated[str, typer.Argument(help="The project name to be looked for (assumes it is a unique ID)")],
        dataset: Annotated[str, typer.Argument(help="The dataset name to be looked for (assumes it is a unique ID)")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):
    
    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    ds_id = get_omero_dataset_id(conn, project, dataset)

    records = [{"type": "dataset", "name": dataset, "id": str(ds_id)}]
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

    conn.close()

@query_app.command("img-ids", help="Query image IDs from OMERO using key-value pairs and tags")
def query_image_ids(
        p_name: Annotated[List[str], typer.Option(default=..., help="Project names to restrict query scope (assumes names are unique IDs), in format '--p-name name1 --p-name name2'")] = [],
        kv_pair: Annotated[List[str], typer.Option(default=..., help="Pairs of key-values for query, in format '--kv-pair key1:value1 --kv-pair key2:value2'")] = [],
        tag: Annotated[List[str], typer.Option(default=..., help="Tag values for query, in format '--tag value1 --tag value2'")] = [],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):
    
    import ezomero

    project_name_list = p_name

    #string format: key1:value1//key2:value2//key3:value3//...
    try:
        parsed_filters = parse_filter_exprs(kv_pair)
    except FilterParseError as exc:
        _handle_cli_error(exc)

    tag_list = tag

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    if len(project_name_list) > 0:
        project_obj_list = []
        for project_name in project_name_list:
            project_obj_list.extend(list(conn.getObjects("Project", attributes={"name": project_name})))
    else:
        project_obj_list = list(conn.getObjects("Project"))

    image_map = {}
    for project in project_obj_list:
        print("[bold blue]Inspecting project: " + str(project.getName()) + " (ID: " + str(project.getId()) + ")")
        for dataset in project.listChildren():
            for image in dataset.listChildren():
                img_path = (project.getName() + "/" + dataset.getName()).replace(" ", "_")
                img_name = image.getName().replace(" ", "_")
                image_map[int(image.getId())] = [img_path, img_name] # id -> path and name

    image_id_list = list(image_map.keys())

    for expr in parsed_filters:
        image_id_list = ezomero.filter_by_kv(conn, image_id_list, key=expr.key, value=str(expr.value), across_groups=True)

    for tag in tag_list:
        image_id_list = ezomero.filter_by_tag_value(conn, image_id_list, tag_value=tag, across_groups=True)

    records = []
    for image_id in image_id_list:
        records.append({
            "id": int(image_id),
            "path": image_map[image_id][0],
            "name": image_map[image_id][1],
        })
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

    conn.close()


@push_app.command("img-file", help="Import an image file into OMERO")
def push_image_file(
        file_path: Annotated[str, typer.Argument(help="Path to the input image file")],
        dataset_id: Annotated[str, typer.Argument(help="ID of target dataset")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    try:
        img_ids = register_image_file_with_dataset_id(file_path, int(dataset_id), omero_username, omero_password, omero_host, str(omero_port), omero_group)
    except (OmeroCliError, ValueError) as exc:
        _handle_cli_error(exc)

    records = [{"type": "image", "name": file_path, "id": str(id_i)} for id_i in img_ids]
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

@push_app.command("img-folder", help="Import a folder containing image files into OMERO")
def push_image_folder(
        folder_path: Annotated[str, typer.Argument(help="Path to the input folder containing image files (depth=1)")],
        dataset_id: Annotated[str, typer.Argument(help="ID of target dataset")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    try:
        img_ids = register_image_folder_with_dataset_id(folder_path, int(dataset_id), omero_username, omero_password, omero_host, str(omero_port), omero_group)
    except (OmeroCliError, ValueError) as exc:
        _handle_cli_error(exc)

    records = [{"type": "image", "name": folder_path, "id": str(id_i)} for id_i in img_ids]
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

@push_app.command("key-value", help="Annotate an image with key-value pairs")
def push_key_value(
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        kv_pair: Annotated[List[str], typer.Option(default=..., help="Key-value pairs in legacy format 'key:value'")],
        validation_policy: Annotated[str, typer.Option("--validation-policy", help="strict or lenient")] = "strict",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):
    
    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    try:
        parsed = parse_filter_exprs(kv_pair)
    except FilterParseError as exc:
        conn.close()
        _handle_cli_error(exc)

    from omero_bifrost.fair.metadata_schema import validate_row

    key_value_data = []
    warnings = []
    for expr in parsed:
        validations = validate_row({expr.key: expr.value})
        invalid = [v for v in validations if v.status == "invalid"]
        if invalid:
            if validation_policy == "strict":
                conn.close()
                _handle_cli_error(ValueError(f"invalid metadata field {expr.key}: {invalid[0].reason_code}"))
            warnings.append(f"Skipping invalid field {expr.key}: {invalid[0].reason_code}")
            continue
        key_value_data.append([expr.key, str(expr.value)])

    for w in warnings:
        print(f"[yellow]WARNING|{w}")

    add_kv_to_image(conn, image_id, key_value_data)

    conn.close()
    _emit_execution_output([{"type": "image", "id": str(image_id), "status": "metadata-updated", "count": len(key_value_data)}], profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

@push_app.command("img-tag", help="Tag an image, create OMERO tag if needed")
def push_image_tag(
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        tag_value: Annotated[str, typer.Argument(help="Text value of OMERO tag")],
        tag_desc: Annotated[str, typer.Option("--desc", "-d", help="Tag description used when creating new tag")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    tags = conn.getObjects("TagAnnotation", attributes={"textValue": tag_value})
    tags = list(tags)

    try:
        if len(tags) > 0:
            tag_id = str(tags[0].getId())
        else:
            tag_id = create_tag(tag_value, tag_desc, omero_username, omero_password, omero_host, str(omero_port), omero_group)

        result = add_tag_to_image(image_id, tag_id, omero_username, omero_password, omero_host, str(omero_port), omero_group)
    except (OmeroCliError, ValueError) as exc:
        conn.close()
        _handle_cli_error(exc)

    conn.close()

    _emit_execution_output([{"type": "image", "id": str(image_id), "tag": tag_value, "stdout": result.stdout, "stderr": result.stderr}], profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)

@push_app.command("file-atch", help="Attach a file to image")
def push_file_atch(
        file_path: Annotated[str, typer.Argument(help="Path to the attachment file")],
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    try:
        img_ann_id = attach_file_to_image(file_path, image_id, omero_username, omero_password, omero_host, str(omero_port), omero_group)
    except (OmeroCliError, ValueError) as exc:
        _handle_cli_error(exc)

    _emit_execution_output([{"type": "file-annotation", "image_id": str(image_id), "id": str(img_ann_id)}], profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path)


@pull_app.command("ome-tiffs", help="Export OME-TIFF image files from a list of OMERO image IDs")
def pull_ome_tiff_files(
        output_path: Annotated[str, typer.Argument(help="Output path, destination of pulled files")],
        img_id: Annotated[List[str], typer.Option(default=..., help="List of image IDs, in format '--img-id id1 --img-id id2'")] = [],
        id_list_path: Annotated[str, typer.Option("--list", "-l", help="Path to a TSV file with image IDs, takes priority if not empty")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    import os

    if id_list_path == "":
        img_id_list = img_id
    else:
        img_map = img_map_from_tsv(id_list_path)
        img_id_list = list(img_map.keys())


    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    file_map = {}
    for img_id in img_id_list:
        image = conn.getObject("Image", img_id)
        if not img_id in file_map.keys():
                file_map[img_id] = str(image.getName()).replace(" ", "_")

    records = []
    for img_id in file_map.keys():
        export_path = os.path.join(output_path, "omero_img_id_" + str(img_id) + "__" + file_map[img_id] + ".ome.tiff")
        try:
            result = export_ome_tiff_file(img_id, export_path, omero_username, omero_password, omero_host, str(omero_port), omero_group)
        except (OmeroCliError, ValueError) as exc:
            conn.close()
            _handle_cli_error(exc)
        records.append({"id": str(img_id), "output_path": export_path, "stdout": result.stdout, "stderr": result.stderr})

    conn.close()
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path, provenance={"command": "pull ome-tiffs"})



@pull_app.command("ome-xmls", help="Export OME-XML metadata files directly as .ome.xml files from a list of OMERO image IDs")
def pull_ome_xml_files(
        output_path: Annotated[str, typer.Argument(help="Output path, destination of pulled XML files")],
        img_id: Annotated[List[str], typer.Option(default=..., help="List of image IDs, in format '--img-id id1 --img-id id2'")] = [],
        id_list_path: Annotated[str, typer.Option("--list", "-l", help="Path to a TSV file with image IDs, takes priority if not empty")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        ):

    import os

    if id_list_path == "":
        img_id_list = img_id
    else:
        img_map = img_map_from_tsv(id_list_path)
        img_id_list = list(img_map.keys())

    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    file_map = {}
    for img_id in img_id_list:
        image = conn.getObject("Image", img_id)
        if not img_id in file_map.keys():
                file_map[img_id] = str(image.getName()).replace(" ", "_")

    records = []
    for img_id in file_map.keys():
        export_path = os.path.join(output_path, "omero_img_id_" + str(img_id) + "__" + file_map[img_id] + ".ome.xml")
        try:
            result = export_ome_xml_file(img_id, export_path, omero_username, omero_password, omero_host, str(omero_port), omero_group)
        except (OmeroCliError, ValueError) as exc:
            conn.close()
            _handle_cli_error(exc)
        records.append({"id": str(img_id), "output_path": export_path, "stdout": result.stdout, "stderr": result.stderr})

    conn.close()
    for record in records:
        print(record["output_path"])
@pull_app.command("orig-files", help="Download original image files from a list of OMERO image IDs")
def pull_original_image_files(
        output_path: Annotated[str, typer.Argument(help="Output path, destination of pulled files")],
        img_id: Annotated[List[str], typer.Option(default=..., help="List of image IDs, in format '--img-id id1 --img-id id2'")] = [],
        id_list_path: Annotated[str, typer.Option("--list", "-l", help="Path to a TSV file with image IDs, takes priority if not empty")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help=CONFIG_HELP_TEXT)] = "./imaging_config.properties",
        server_profile: Annotated[str, typer.Option("--server-profile", "-s", help=SERVER_PROFILE_HELP_TEXT)] = "default",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output JSON file")] = "./omero_bifrost_output.json",
        to_file: Annotated[bool, typer.Option(help="write JSON output to file")] = False,
        to_console: Annotated[bool, typer.Option("--to-console", help="Print JSON output to console")]=False
        ):

    import os

    if id_list_path == "":
        img_id_list = img_id
    else:
        img_map = img_map_from_tsv(id_list_path)
        img_id_list = list(img_map.keys())


    omero_username, omero_password, omero_host, omero_port, omero_group = _load_omero_config(config_file_path, server_profile)

    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port), omero_group)

    orig_file_map = {}
    for img_id in img_id_list:
        image = conn.getObject("Image", img_id)

        if len(image.getFileset().listFiles()) > 0:
            orig_file_obj = image.getFileset().listFiles()[0] # assume first file is original image file
            orig_file_id = str(orig_file_obj.getId())
            if not orig_file_id in orig_file_map.keys():
                orig_file_map[orig_file_id] = str(orig_file_obj.getName())

    records = []
    for orig_file_id in orig_file_map.keys():
        download_path = os.path.join(output_path, "omero_file_id_" + str(orig_file_id) + "__" + orig_file_map[orig_file_id])
        try:
            result = download_original_image_file(orig_file_id, download_path, omero_username, omero_password, omero_host, str(omero_port), omero_group)
        except (OmeroCliError, ValueError) as exc:
            conn.close()
            _handle_cli_error(exc)
        records.append({"id": str(orig_file_id), "output_path": download_path, "stdout": result.stdout, "stderr": result.stderr})

    conn.close()
    _emit_execution_output(records, profile=server_profile, to_file=to_file, to_console=to_console, output_file_path=output_file_path, provenance={"command": "pull orig-files"})
