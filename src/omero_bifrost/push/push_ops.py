from omero_bifrost.utils.util_ops import omero_connect
from omero_bifrost.utils.omero_cli_runner import (
    parse_file_annotation_id,
    parse_image_annotation_link_id,
    parse_image_ids,
    parse_original_file_id,
    parse_tag_annotation_id,
    run_omero_cli,
)


def _base_omero_cmd(usr, pwd, host, port=4064, group=None):
    args = ["-s", host, "-p", str(port), "-u", usr, "-w", pwd]
    if group is not None:
        args.extend(["-g", str(group)])
    return args


def register_image_file_with_dataset_id(file_path, dataset_id, usr, pwd, host, port=4064, group=None):
    if int(dataset_id) < 0:
        raise ValueError("dataset_id must be a non-negative integer.")

    cmd = [
        "omero",
        "import",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "-d",
        str(int(dataset_id)),
        str(file_path),
    ]
    return parse_image_ids(run_omero_cli(cmd))


def register_image_folder_with_dataset_id(folder_path, dataset_id, usr, pwd, host, port=4064, group=None):
    if int(dataset_id) < 0:
        raise ValueError("dataset_id must be a non-negative integer.")

    cmd = [
        "omero",
        "import",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "-d",
        str(int(dataset_id)),
        "--depth",
        "1",
        str(folder_path),
    ]
    return parse_image_ids(run_omero_cli(cmd))


def attach_file_to_image(file_path, image_id, usr, pwd, host, port=4064, group=None):
    upload_cmd = [
        "omero",
        "upload",
        *_base_omero_cmd(usr, pwd, host, port, group),
        str(file_path),
    ]
    original_file_id = parse_original_file_id(run_omero_cli(upload_cmd))

    file_ann_cmd = [
        "omero",
        "obj",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "new",
        "FileAnnotation",
        f"file=OriginalFile:{original_file_id}",
    ]
    file_ann_id = parse_file_annotation_id(run_omero_cli(file_ann_cmd))

    image_ann_link_cmd = [
        "omero",
        "obj",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "new",
        "ImageAnnotationLink",
        f"parent=Image:{image_id}",
        f"child=FileAnnotation:{file_ann_id}",
    ]
    return parse_image_annotation_link_id(run_omero_cli(image_ann_link_cmd))


def create_tag(tag_value, tag_desc, usr, pwd, host, port=4064, group=None):
    cmd = [
        "omero",
        "tag",
        "create",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "--name",
        str(tag_value),
        "--desc",
        str(tag_desc),
    ]
    return parse_tag_annotation_id(run_omero_cli(cmd))


def add_tag_to_image(image_id, tag_id, usr, pwd, host, port=4064, group=None):
    cmd = [
        "omero",
        "tag",
        "link",
        *_base_omero_cmd(usr, pwd, host, port, group),
        f"Image:{image_id}",
        str(tag_id),
    ]
    return run_omero_cli(cmd)


def add_kv_to_image(conn, image_id, key_value_data):
    import omero

    map_ann = omero.gateway.MapAnnotationWrapper(conn)
    namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
    map_ann.setNs(namespace)
    map_ann.setValue(key_value_data)
    map_ann.save()

    image = conn.getObject("Image", image_id)
    image.linkAnnotation(map_ann)

    return 0


########################################
#functions to push numpy arrays

def generate_array_plane(new_img):
    """
    TODO
    """

    img_shape = new_img.shape
    size_z = img_shape[4]
    size_t = img_shape[0]
    size_c = img_shape[1]

    for z in range(size_z):              # all Z sections
        for c in range(size_c):          # all channels
            for t in range(size_t):      # all time-points

                new_plane = new_img[t, c, :, :, z]
                yield new_plane


def create_array(conn, img, img_name, img_desc, ds):
    """
    TODO
    """

    dims = img.shape
    z = dims[4]
    t = dims[0]
    c = dims[1]

    new_img = conn.createImageFromNumpySeq(generate_array_plane(img),
                                           img_name,
                                           z, c, t,
                                           description=img_desc,
                                           dataset=ds)

    return new_img.getId()


def register_image_array(img, img_name, img_desc, project_id, sample_id, usr, pwd, host, port=4064):
    """
    This function imports a 5D (time-points, channels, x, y, z) numpy array of an image
    to an omero server using the OMERO Python bindings
    """

    img_id = -1
    save_flag = 0

    conn = omero_connect(usr, pwd, host, str(port))

    for project in conn.getObjects("Project"):
        if project.getName() == project_id:
            for dataset in project.listChildren():
                if dataset.getName() == sample_id:

                    img_id = create_array(conn, img, img_name, img_desc, dataset)

                    save_flag = 1
                    break
        if save_flag == 1:
            break

    return int(img_id)
