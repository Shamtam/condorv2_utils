from gimpfu import *
from math import pi

import codecs
import os
import re
 
def downsize_dds(filename, size):

    flist = pdb.file_glob(filename, 0)

    for fname in flist[1]:
        inpath = os.path.abspath(fname)
        outpath = os.path.splitext(fname)[0] + '.dds'

        img = pdb.file_dds_load(inpath, inpath, 1, 0)
        drawable = pdb.gimp_image_get_active_layer(img)

        pdb.gimp_context_set_interpolation(2) # cubic interpolation

        pdb.gimp_image_scale(img, size, size)

        pdb.file_dds_save(img, drawable, outpath, outpath, 
            2, # dxt3 compression
            1, # mipmaps
            0, # selected layer
            0, # format
            -1, # transparency index
            8, # kaiser mipmap filter
            0,
            0,
            0,
            0,
            0,
            0,
            0
        )

        pdb.gimp_image_delete(img)

register(
    # procedure name in PDB
    "downsize_dds",
    # brief description
    "Downsize a .dds file",
    # help message
    "Downsize the square input file to the given dimension. Uses glob patterns for filename input.",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "Downsize DDS",
    # image type
    None,
    # input parameters
    [
        (PF_STRING, "fname", "fname", None),
        (PF_INT, "size", "size", 256)
    ],
    # output parameters
    [],
    # callback
    downsize_dds,
    # menu
    menu='' # command-line usage only
)

def convert_to_dds(filename):

    flist = pdb.file_glob(filename, 0)

    for fname in flist[1]:
        inpath = os.path.abspath(fname)
        outpath = os.path.splitext(fname)[0] + '.dds'

        img = pdb.gimp_file_load(inpath, inpath)
        drawable = pdb.gimp_image_get_active_layer(img)

        pdb.file_dds_save(img, drawable, outpath, outpath, 
            2, # dxt3 compression
            1, # mipmaps
            0, # selected layer
            0, # format
            -1, # transparency index
            8, # kaiser mipmap filter
            0,
            0,
            0,
            0,
            0,
            0,
            0
        )

        pdb.gimp_image_delete(img)

register(
    # procedure name in PDB
    "convert_to_dds",
    # brief description
    "Convert to .dds",
    # help message
    "Convert input image files into dxt3 .dds. Uses glob patterns for filename input.",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "RGB/Alpha -> DDS",
    # image type
    None,
    # input parameters
    [
        (PF_STRING, "fname", "fname", None),
    ],
    # output parameters
    [],
    # callback
    convert_to_dds,
    # menu
    menu='' # command-line usage only
)

def merge_bmp_alpha_to_dds(rgb_pattern, alpha_pattern):

    bmp_list = pdb.file_glob(rgb_pattern, 0)[1]
    alpha_list = [os.path.splitext(os.path.basename(x))[0] for x in pdb.file_glob(alpha_pattern, 0)[1]]

    infiles = []

    for bmpf in bmp_list:
        if 'a{}'.format(os.path.splitext(os.path.basename(bmpf))[0]) in alpha_list:
            infiles.append(bmpf)

    print

    for fname in infiles:
        print 'Processing file {}'.format(fname)

        inpath = os.path.abspath(fname)
        alpha_inpath = os.path.abspath('a{}'.format(os.path.basename(fname)))
        outpath = os.path.splitext(fname)[0] + '.dds'

        rgb = pdb.file_bmp_load(inpath, inpath)
        rgb_drawable = pdb.gimp_image_get_active_layer(rgb)

        alpha = pdb.file_bmp_load(alpha_inpath, alpha_inpath)
        alpha_drawable = pdb.gimp_image_get_active_layer(alpha)

        if(not pdb.gimp_drawable_has_alpha(rgb_drawable)):
            pdb.gimp_layer_add_alpha(rgb_drawable)
        
        mask = pdb.gimp_layer_create_mask(rgb_drawable, ADD_MASK_WHITE)
        pdb.gimp_layer_add_mask(rgb_drawable, mask)
        pdb.gimp_layer_set_edit_mask(rgb_drawable, True)

        pdb.gimp_edit_copy(alpha_drawable)

        paste = pdb.gimp_edit_paste(mask, True)
        pdb.gimp_floating_sel_anchor(paste)
        pdb.gimp_layer_remove_mask(rgb_drawable, MASK_APPLY)

        print 'Merged a{0} into alpha layer of {0}'.format(fname)

        pdb.file_dds_save(rgb, rgb_drawable, outpath, outpath, 
            2, # dxt3 compression
            1, # mipmaps
            0, # selected layer
            2, # format RGBA4
            -1, # transparency index
            3, # 3 - triangle, 8 - kaiser mipmap filter
            0,
            0,
            0,
            0,
            0,
            0,
            0
        )

        print 'Saved {}'.format(os.path.basename(outpath))
        print

        del mask
        pdb.gimp_image_delete(rgb)
        pdb.gimp_image_delete(alpha)

register(
    # procedure name in PDB
    "merge_bmp_alpha_to_dds",
    # brief description
    "RGB/Alpha BMPs to DDS",
    # help message
    "Combine RGB and Grayscale (alpha) bmp files into single dxt3 .dds. Uses glob patterns for filename input. Assumes the alpha bmp filename is simply the name of the RGB bmp file with a preceding `a` (e.g. an RGB file 1234.bmp would correspond to an alpha file a1234.bmp).",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "RGB/Alpha -> DDS",
    # image type
    None,
    # input parameters
    [
        (PF_STRING, "rgb_pattern", "rgb_pattern", None),
        (PF_STRING, "alpha_pattern", "alpha_pattern", None),
    ],
    # output parameters
    [],
    # callback
    merge_bmp_alpha_to_dds,
    # menu
    menu='' # command-line usage only
)

# forest patch dimensions
_forest_map_x = 512
_forest_map_y = 512

# forest patch opacity overlaid over texture
_forest_opacity = 25.0

# map 8bpp forest map pixels into 32bpp pixels as follows
# raw -> RR GG BB AA
# x00 -> 00 00 00 ff make no-trees black
# x01 -> ff 00 00 ff make coniferous trees red
# x02 -> 00 00 ff ff make deciduous trees blue
_forest_pixel_match = re.compile('[\0-\xff][\0-\xff][\0-\xff]\xff')
_forest_pixel_empty = b'\x00\x00\x00\xff'
_forest_pixel_coniferous = b'\xff\x00\x00\xff'
_forest_pixel_deciduous = b'\x00\x00\xff\xff'
_forest_byte_empty = b'\x00'
_forest_byte_coniferous = b'\x01'
_forest_byte_deciduous = b'\x02'

def file_condor_forest_load(filename, raw_filename):
    # extract and determine directories for forest/texture files
    forest_dir = os.path.dirname(os.path.abspath(filename))
    texture_dir = os.path.join(forest_dir, '..', 'Textures')
    patchnum = os.path.splitext(os.path.basename(filename))[0]

    forest_path = os.path.abspath(filename)
    texture_path = os.path.abspath(os.path.join(texture_dir, 't{}.dds'.format(patchnum)))

    # load texture patch, resize it to forest map size, rename it
    img = pdb.file_dds_load(texture_path, texture_path, False, False)
    pdb.gimp_image_scale(img, _forest_map_x, _forest_map_y)
    texture_layer = img.layers[0]
    texture_layer.name = 'texture'

    # load forest map bytes
    with open(forest_path, 'rb') as fp:
        forest_bytes = fp.read()

    # expand and convert 8bit pixels to 32bit RGBA pixels
    forest_bytes = forest_bytes.replace(_forest_byte_empty, _forest_pixel_empty)
    forest_bytes = forest_bytes.replace(_forest_byte_coniferous, _forest_pixel_coniferous)
    forest_bytes = forest_bytes.replace(_forest_byte_deciduous, _forest_pixel_deciduous)

    # create new layer for forest from bytes
    forest_layer = pdb.gimp_layer_new(img, _forest_map_x, _forest_map_y, 1, 'forest', _forest_opacity, 0)
    region = forest_layer.get_pixel_rgn(0, 0, _forest_map_x, _forest_map_y, True, False)
    region[:,:] = forest_bytes

    # add layer to image
    img.insert_layer(forest_layer)

    # rotate layer 90deg CCW
    pdb.gimp_item_transform_rotate(forest_layer, -0.5*pi, True, 0, 0)

    # flip layer over vertical axis
    pdb.gimp_item_transform_flip_simple(forest_layer, ORIENTATION_HORIZONTAL, True, 0.0)

    return img

register(
    # procedure name in PDB
    "file_condor_forest_load",
    # brief description
    "Load Condor forest map file",
    # help message
    "Loads a 512x512 Condor forest map file and overlays it as a layer with {}% opacity over its associated texture patch. Modify the `forest` layer only, and make sure to not modify its alpha channel! Use pure black (RGB = 0, 0, 0) to signify no trees. Use pure red (RGB = 255, 0, 0) to signify coniferous trees. Use pure blue (RGB = 0, 0, 255) to signify deciduous trees.".format(_forest_opacity),
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "Condor forest map file (.for)",
    # image type
    None,
    # input parameters
    [
        (PF_STRING, "filename", "filename", None),
        (PF_STRING, "raw-filename", "raw-filename", None),
    ],
    # output parameters
    [
        (PF_IMAGE, "image", "image", None),
    ],
    # callback
    file_condor_forest_load,
    # load handler
    on_query=lambda: pdb.gimp_register_load_handler('file-condor-forest-load', 'for', ''),
    # menu
    menu='<Load>'
)

def file_condor_forest_save(image, drawable, filename, raw_filename):
    try:
        # duplicate image
        img = pdb.gimp_image_duplicate(image)

        # get forest layer
        layer_names = [layer.name for layer in img.layers]

        if 'forest' not in layer_names:
            pdb.gimp_message('Invalid layer names, must have "forest" layer')

        forest_layer = img.layers[layer_names.index('forest')]
        
        # flip layer over vertical axis
        pdb.gimp_item_transform_flip_simple(forest_layer, ORIENTATION_HORIZONTAL, True, 0.0)

        # rotate layer 90deg CW
        pdb.gimp_item_transform_rotate(forest_layer, 0.5*pi, True, 0, 0)

        # extract and convert 32bpp to Condor format
        forest_bytes = forest_layer.get_pixel_rgn(0, 0, _forest_map_x, _forest_map_y, True, False)[:,:]

        # convert pixels from 32bit to 8bit
        def convert_pixel(m):
            if m.group(0) == _forest_pixel_coniferous:
                return _forest_byte_coniferous
            elif m.group(0) == _forest_pixel_deciduous:
                return _forest_byte_deciduous
            else:
                return _forest_byte_empty

        forest_bytes = _forest_pixel_match.sub(convert_pixel, forest_bytes)
        
        # save file
        with open(os.path.abspath(filename), 'wb') as fp:
            fp.write(forest_bytes)
        
        # delete duplicated image
        pdb.gimp_image_delete(img)

    except Exception as e:
        pdb.gimp_message('Unable to export Condor forest map')
        raise

register(
    # procedure name in PDB
    "file-condor-forest-save",
    # brief description
    "Export a Condor forest map file",
    # help message
    "Exports a 512x512 Condor forest map file which was previously loaded into GIMP.",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "Condor forest map file (.for)",
    # image type
    None,
    # input parameters
    [
        (PF_IMAGE, "image", "image", None),
        (PF_DRAWABLE, "drawable", "drawable", None),
        (PF_STRING, "filename", "filename", None),
        (PF_STRING, "raw-filename", "raw-filename", None),
    ],
    # output parameters
    [],
    # callback
    file_condor_forest_save,
    # save handler
    on_query=lambda: pdb.gimp_register_save_handler('file-condor-forest-save', 'for', ''),
    # menu
    menu='<Save>',
)

# thermal map opacity overlaid over texture
_thermal_opacity = 25.0

def file_condor_thermal_load(filename, raw_filename):
    # extract and determine filepaths for thermal/texture files
    thermal_path = os.path.abspath(filename)

    # load thermal map bytes
    with open(thermal_path, 'rb') as fp:
        thermal_bytes = fp.read()

    x = int(codecs.encode(thermal_bytes[0:3], 'hex_codec'), 16)
    y = int(codecs.encode(thermal_bytes[4:7], 'hex_codec'), 16)
    map_bytes = thermal_bytes[8:]

    # load texture bmp and rename it
    img = pdb.gimp_image_new(x, y, 1) # 1 = grayscale image
    layer = pdb.gimp_layer_new(img, x, y, 2, 'thermal', 100.0, 0) # 2 - grayscale
    img.insert_layer(layer)
    region = layer.get_pixel_rgn(0, 0, x, y, True, False)
    region[:,:] = map_bytes

    # rotate layer 180deg
    pdb.gimp_item_transform_rotate(layer, pi, True, 0, 0)

    return img

register(
    # procedure name in PDB
    "file_condor_thermal_load",
    # brief description
    "Load Condor thermal map file",
    # help message
    "Loads a Condor thermal map file as a grayscale 8bpp image and overlays it as a layer with the viewer map",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "Condor thermal map file (.tdm)",
    # image type
    None,
    # input parameters
    [
        (PF_STRING, "filename", "filename", None),
        (PF_STRING, "raw-filename", "raw-filename", None),
    ],
    # output parameters
    [
        (PF_IMAGE, "image", "image", None),
    ],
    # callback
    file_condor_thermal_load,
    # load handler
    on_query=lambda: pdb.gimp_register_load_handler('file-condor-thermal-load', 'tdm', ''),
    # menu
    menu='<Load>'
)

def file_condor_thermal_save(image, drawable, filename, raw_filename):
    try:
        # duplicate image
        img = pdb.gimp_image_duplicate(image)
        thermal_layer = img.layers[0]

        # rotate layer 180deg
        pdb.gimp_item_transform_rotate(thermal_layer, pi, True, 0, 0)

        x = pdb.gimp_image_width(image)
        y = pdb.gimp_image_height(image)
        x_bytes = codecs.decode('{:08x}'.format(x), 'hex_codec')[::-1]
        y_bytes = codecs.decode('{:08x}'.format(y), 'hex_codec')[::-1]

        # extract and convert 32bpp to Condor format
        raw_bytes = thermal_layer.get_pixel_rgn(0, 0, x, y, True, False)[:,:]
        thermal_bytes = x_bytes + y_bytes + raw_bytes[::2]
        
        # save file
        with open(os.path.abspath(filename), 'wb') as fp:
            fp.write(thermal_bytes)
        
        # delete duplicated image
        pdb.gimp_image_delete(img)

    except Exception as e:
        pdb.gimp_message('Unable to export Condor thermal map')
        raise

register(
    # procedure name in PDB
    "file-condor-thermal-save",
    # brief description
    "Export a Condor thermal map file",
    # help message
    "Exports a Condor thermal map file which was previously loaded into GIMP.",
    # author
    "Shamit Som",
    # copyright
    "Shamit Som",
    # year
    "2020",
    # label
    "Condor thermal map file (.tdm)",
    # image type
    None,
    # input parameters
    [
        (PF_IMAGE, "image", "image", None),
        (PF_DRAWABLE, "drawable", "drawable", None),
        (PF_STRING, "filename", "filename", None),
        (PF_STRING, "raw-filename", "raw-filename", None),
    ],
    # output parameters
    [],
    # callback
    file_condor_thermal_save,
    # save handler
    on_query=lambda: pdb.gimp_register_save_handler('file-condor-thermal-save', 'tdm', ''),
    # menu
    menu='<Save>',
)

main()
