from omero_bifrost.utils.omero_cli_runner import run_omero_cli


def _base_omero_cmd(usr, pwd, host, port=4064, group=None):
    args = ["-s", host, "-p", str(port), "-u", usr, "-w", pwd]
    if group is not None:
        args.extend(["-g", str(group)])
    return args


def download_original_image_file(orig_file_id, download_path, usr, pwd, host, port=4064, group=None):
    if int(orig_file_id) < 0:
        raise ValueError("orig_file_id must be a non-negative integer.")

    cmd = [
        "omero",
        "download",
        *_base_omero_cmd(usr, pwd, host, port, group),
        str(orig_file_id),
        str(download_path),
    ]
    return run_omero_cli(cmd)


def export_ome_tiff_file(image_id, download_path, usr, pwd, host, port=4064, group=None):
    import os

    if int(image_id) < 0:
        raise ValueError("image_id must be a non-negative integer.")

    name, ext = os.path.splitext(download_path)
    if ext not in {".tif", ".tiff"}:
        download_path = name + ".ome.tiff"

    cmd = [
        "omero",
        "export",
        *_base_omero_cmd(usr, pwd, host, port, group),
        "--file",
        str(download_path),
        "--type",
        "TIFF",
        f"Image:{image_id}",
    ]
    return run_omero_cli(cmd)


########################################
#functions to pull numpy arrays

def get_image_array(conn, image_id):
    """
    This function retrieves an image from an OMERO server as a numpy array
    TODO
    """

    import numpy as np

    image = conn.getObject("Image", image_id)

    #construct numpy array (t, c, x, y, z)

    size_x = image.getSizeX()
    size_y = image.getSizeY()
    size_z = image.getSizeZ()
    size_c = image.getSizeC()
    size_t = image.getSizeT()

    # X and Y fields have to be aligned this way since during generation of the image from the numpy array the 2darray is expected to be (Y,X)
    # See Documentation here https://downloads.openmicroscopy.org/omero/5.5.1/api/python/omero/omero.gateway.html#omero.gateway._BlitzGateway
    hypercube = np.zeros((size_t, size_c, size_y, size_x, size_z))

    pixels = image.getPrimaryPixels()

    for t in range(size_t):
        for c in range(size_c):
            for z in range(size_z):
                plane = pixels.getPlane(z, c, t)      # get a numpy array.
                hypercube[t, c, :, :, z] = plane

    return hypercube
