#!/usr/bin/env python

"""
Description: Render a list of VTK data  and (or) a nifti image, then view or save PNG or save WebGL.
The code is modified from ITKExamples.

When an output PNG or WebGL file is not specified, an interactive windows is
displayed.  To get the camera position from the interactive window, press the
"c" key.

e: exit the application
q: quit the application

s: surface representation
w: wireframe representation

Examples:
VTKPolyData.py --vtk file1.vtk file2.vtk --image im.nii.gz
VTKPolyData.py --vtk file1.vtk file2.vtk --vtk2 tensor.vtk --image im.nii.gz
VTKPolyData.py --vtk file1.vtk file2.vtk --image im.nii.gz --sliceX 50 --sliceY 40 --sliceZ 60
VTKPolyData.py --vtk file1.vtk file2.vtk --image im.nii.gz --png out.png

Author(s): Jian Cheng (jian.cheng.1983@gmail.com)
"""

import argparse
import sys

import vtk
import utlVTK

import utlDMRITool as utl

def arg_values(value, typefunc, numberOfValues):
    '''set arguments based using comma. If numberOfValues<0, it supports arbitrary number of inputs.'''
    value = value.strip()
    if value[0]=='(' and value[-1]==')':
        value = value[1:-1]
    values = value.split(',')
    if numberOfValues > 0 and len(values) != numberOfValues:
        raise argparse.ArgumentError
    return map(typefunc, values)


def arg_bool(parser, boolarg, defaultbool, helpdoc):
    '''set bool argment'''
    group = parser.add_mutually_exclusive_group()
    if defaultbool:
        group.add_argument('--' + boolarg, dest=boolarg, action='store_true', help='with ' + boolarg + ' (default). ' + helpdoc)
        group.add_argument('--no-' + boolarg, dest=boolarg, action='store_false', help='without ' + boolarg + '. ' + helpdoc)
    else:
        group.add_argument('--no-' + boolarg, dest=boolarg, action='store_false', help='without ' + boolarg + ' (default). ' + helpdoc)
        group.add_argument('--' + boolarg, dest=boolarg, action='store_true', help='with ' + boolarg + '. ' + helpdoc)
    exec ''.join(['parser.set_defaults(', boolarg, '=', 'True' if defaultbool else 'False', ')'])


def main():

    # work for arguments with minus sign
    for i, arg in enumerate(sys.argv):
        if (arg[0] == '-') and arg[1].isdigit():
            sys.argv[i] = ' ' + arg

    parser = argparse.ArgumentParser(description=utl.app_doc(__doc__),  formatter_class=argparse.RawTextHelpFormatter)

    # vtk data
    parser.add_argument('--vtk', help='VTK PolyData (.vtk, .vtp, etc) input, multiple inputs. Use HueRange=(0.6667,0)', nargs='*')
    arg_bool(parser, 'frame', False, 'Visualize frame.')
    arg_bool(parser, 'surface', True, 'Visualize surface.')
    arg_bool(parser, 'normal', True, 'Use vtkPolyDataNormals for polydata visualization.')
    arg_bool(parser, 'lighting', True, 'Lighting.')
    parser.add_argument('--scalar-range', help='lowest and highest scalar values for the vtk coloring. It is used when scalar dimention is 1. If not set, use the range of the scalar values. \n\
                        Default: (-1,-1) means the (min,max)', default=(-1.0, -1.0),
                        type=(lambda value: arg_values(value, float, 2)), metavar=('lowest,highest'))
    #  parser.add_argument('--hue-range', help='hue range for the vtk coloring. For tensors coloring by directions, use (0.0,1.0). Default: (0.6667,0.0)', default=(0.6667,0.0),
    #                      type=(lambda value: arg_values(value, float, 2)), metavar=('lowest,highest'))

    # only used for dti tensors colored by directions
    parser.add_argument('--vtk2', help='VTK readPolydata. Use HueRange=(0,1). Specified for meshes from tensors colored by directions, generated by MeshFromTensors.', nargs=1)

    # nifti data
    parser.add_argument('--image', help='nifti image file', nargs=1)
    parser.add_argument('--image-flip', help='flip x,y,z axis in image. Default: (1,1,1)', default=(1, 1, 1),
                        type=(lambda value: arg_values(value, int, 3)), metavar=('flipZ,flipY,flipZ'))
    parser.add_argument('--image-origin', help='Set image origin as given values.',
                        type=(lambda value: arg_values(value, float, 3)), metavar=('ox,oy,oz'))
    parser.add_argument('--image-opacity', help='image opacity', type=float, metavar=('opacity'), default=1.0)
    arg_bool(parser, 'interpolate', False, 'Image interpolation.')
    parser.add_argument('--sliceX', help='x-axis slices of the image', type=(lambda value: arg_values(value, int, -1)), metavar=('x1,x2,...'))
    parser.add_argument('--sliceY', help='y-axis slices of the image', type=(lambda value: arg_values(value, int, -1)), metavar=('y1,y2,...'))
    parser.add_argument('--sliceZ', help='z-axis slices of the image', type=(lambda value: arg_values(value, int, -1)), metavar=('z1,z2,...'))
    parser.add_argument('--image-range', help='lowest and highest contrast value for the image visualization. If not set, use the minimal and maximal values in the image. \n\
                        Default: (-1,-1) means the (min,max) from the image', default=(-1.0, -1.0),
                        type=(lambda value: arg_values(value, float, 2)), metavar=('lowest,highest'))

    # camera
    parser.add_argument('--angle', help='azimuth and elevation for camera',
                        type=(lambda value: arg_values(value, float, 2)), metavar=('azimuth,elevation'))
    parser.add_argument('--position', help='Camera Position',
                        type=(lambda value: arg_values(value, float, 3)), metavar=('x,y,z'))
    parser.add_argument('--focal-point', help='Camera FocalPoint',
                        type=(lambda value: arg_values(value, float, 3)), metavar=('x,y,z'))
    parser.add_argument('--view-up', help='Camera ViewUp',
                        type=(lambda value: arg_values(value, float, 3)), metavar=('x,y,z'))
    parser.add_argument('--bgcolor', help='back ground color',
                        type=(lambda value: arg_values(value, float, 3)), metavar=('r,g,b'), default=(0, 0, 0))
    parser.add_argument('--size', help='Window size in pixels. Default: (600,600)', default=(600, 600),
                        type=(lambda value: arg_values(value, int, 2)), metavar=('width,height'))
    parser.add_argument('--clipping-range', help='Camera clipping range',
                        type=(lambda value: arg_values(value, float, 2)), metavar=('near,far'))

    parser.add_argument('--png', help='Output PNG file',
                        metavar='file.png')
    parser.add_argument('--zoom', help='camera zoom factor',
                        type=float, metavar=('zoomfactor'), default=1.0)
    parser.add_argument('--webgl', help='File prefix for WebGL output',
                        metavar='webglFilePrefix')

    parser.add_argument('--verbose', '-v', dest='verbose', action='store_true', help='verbose information')

    args = parser.parse_args()
    if args.verbose:
        print args

    if not args.vtk and not args.vtk2 and not args.image:
        print "need inputs for --vtk and (or) --vtk2 and (or) --image"
        raise argparse.ArgumentError

    render_window = vtk.vtkRenderWindow()
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(args.bgcolor[0], args.bgcolor[1], args.bgcolor[2])
    render_window.AddRenderer(renderer)
    render_window.SetSize(args.size)

    vtkfiles=[]
    if args.vtk:
        vtkfiles = vtkfiles + args.vtk
    if args.vtk2:
        vtkfiles = vtkfiles + args.vtk2

    if args.vtk or args.vtk2:
        for inputFile in vtkfiles:
            polyData = utlVTK.readPolydata(inputFile)

            if args.frame:
                frame_mapper = vtk.vtkDataSetMapper()
                frame_mapper.SetInputData(polyData)
                frame_actor = vtk.vtkLODActor()
                frame_actor.SetMapper(frame_mapper)
                prop = frame_actor.GetProperty()
                prop.SetRepresentationToWireframe()
                prop.SetColor(0.0, 0.0, 1.0)
                renderer.AddActor(frame_actor)

            if args.surface:
                surface_mapper = vtk.vtkDataSetMapper()

                if args.normal and polyData.GetPointData().GetNormals() is None:
                    polyDataNormals = vtk.vtkPolyDataNormals()
                    try:
                        polyDataNormals.SetInputData(polyData)
                    except:
                        polyDataNormals.SetInput(polyData)
                    # polyDataNormals.SetFeatureAngle(90.0)
                    surface_mapper.SetInputConnection(
                        polyDataNormals.GetOutputPort())
                else:
                    try:
                        surface_mapper.SetInputData(polyData)
                    except:
                        surface_mapper.SetInput(polyData)

                # lut when scalar is used for colors
                if polyData.GetPointData().GetScalars() and polyData.GetPointData().GetScalars().GetNumberOfComponents()==1:
                    lut = vtk.vtkLookupTable()
                    if args.scalar_range[0] == -1 or args.scalar_range[1] == -1:
                        valueRange = polyData.GetScalarRange()
                    vr0 = args.scalar_range[0] if args.scalar_range[0] != -1 else valueRange[0]
                    vr1 = args.scalar_range[1] if args.scalar_range[1] != -1 else valueRange[1]
                    valueRange = (vr0, vr1)
                    lut.SetTableRange(valueRange[0], valueRange[1])
                    if args.vtk2 and inputFile in args.vtk2:
                        #  for tensors colored by directions
                        lut.SetHueRange(0.0,1.0)
                    else:
                        lut.SetHueRange(0.6667, 0)
                    #  lut.SetHueRange(args.hue_range[0], args.hue_range[1])
                    lut.SetRampToLinear()
                    lut.Build()

                    surface_mapper.SetLookupTable(lut)
                    surface_mapper.SetScalarRange(valueRange[0], valueRange[1])

                surface_actor = vtk.vtkLODActor()
                surface_actor.SetMapper(surface_mapper)
                prop = surface_actor.GetProperty()
                prop.SetRepresentationToSurface()
                if not args.lighting:
                    prop.LightingOff()
                renderer.AddActor(surface_actor)

    if args.image:

        imagefile = args.image[0]
        reader = vtk.vtkNIFTIImageReader()
        reader.SetFileName(imagefile)
        reader.Update()

        # set origin based on itk::NiftiImageIO
        im = reader.GetOutput()
        niftiheader = reader.GetNIFTIHeader()
        #  print (niftiheader)

        if args.image_origin is None:
            if (niftiheader.GetSFormCode()>0):
                im.SetOrigin(niftiheader.GetSRowX()[3], niftiheader.GetSRowY()[3], niftiheader.GetSRowZ()[3]);
            elif (niftiheader.GetQFormCode()>0):
                im.SetOrigin(-niftiheader.GetQOffsetX(), -niftiheader.GetQOffsetY(), niftiheader.GetQOffsetZ())
        else:
            im.SetOrigin(args.image_origin[0], args.image_origin[1], args.image_origin[2]);


        # for 2D image, set sliceX or sliceY or slizeZ automatically
        x1, x2, y1, y2, z1, z2 = im.GetExtent()
        if x1 == x2:
            args.sliceX = [x1]
        if y1 == y2:
            args.sliceY = [y1]
        if z1 == z2:
            args.sliceZ = [z1]

        # for 3D image, slice needs to be set manually
        if not args.sliceX and not args.sliceY and not args.sliceZ:
            raise Exception("need to choose one or more slice for the 3D image!\n")

        # flip image if needed
        image = utlVTK.flipVTKImageData(im, args.image_flip)

        # opacity
        image_opacity = args.image_opacity

        # lut
        lut = vtk.vtkLookupTable()
        if args.image_range[0] == -1 or args.image_range[1] == -1:
            valueRange = image.GetScalarRange()
        vr0 = args.image_range[0] if args.image_range[0] != -1 else valueRange[0]
        vr1 = args.image_range[1] if args.image_range[1] != -1 else valueRange[1]
        valueRange = (vr0, vr1)
        lut.SetTableRange(valueRange[0], valueRange[1])
        lut.SetSaturationRange(0, 0)
        lut.SetHueRange(0, 0)
        lut.SetValueRange(0, 1)
        lut.SetRampToLinear()
        lut.Build()

        if args.verbose:
            print('image_opacity: ', image_opacity)
            print('valueRange: ', valueRange)
            if args.sliceX:
                print('sliceX: ', args.sliceX)
            if args.sliceY:
                print('sliceY: ', args.sliceY)
            if args.sliceZ:
                print('sliceZ: ', args.sliceZ)

        planeColors = vtk.vtkImageMapToColors()
        planeColors.SetInputData(image)
        planeColors.SetLookupTable(lut)
        planeColors.Update()

        assem = vtk.vtkAssembly()

        if args.sliceX:
            for x in args.sliceX:
                act = vtk.vtkImageActor()
                act.SetInputData(planeColors.GetOutput())
                act.SetDisplayExtent(x, x, y1, y2, z1, z2)
                act.InterpolateOn() if args.interpolate else act.InterpolateOff()
                act.SetOpacity(image_opacity)
                assem.AddPart(act)

        if args.sliceY:
            for y in args.sliceY:
                act = vtk.vtkImageActor()
                act.SetInputData(planeColors.GetOutput())
                act.SetDisplayExtent(x1, x2, y, y, z1, z2)
                act.InterpolateOn() if args.interpolate else act.InterpolateOff()
                act.SetOpacity(image_opacity)
                assem.AddPart(act)

        if args.sliceZ:
            for z in args.sliceZ:
                act = vtk.vtkImageActor()
                act.SetInputData(planeColors.GetOutput())
                act.SetDisplayExtent(x1, x2, y1, y2, z, z)
                act.InterpolateOn() if args.interpolate else act.InterpolateOff()
                act.SetOpacity(image_opacity)
                assem.AddPart(act)

        renderer.AddViewProp(assem)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)
    interactorStyle = render_window_interactor.GetInteractorStyle()
    interactorStyle.SetCurrentStyleToTrackballCamera()

    render_window_interactor.Initialize()

    render_window.Render()

    camera = renderer.GetActiveCamera()

    def print_camera_position(interactor, event):
        def cmd_line_friendly(xyz):
            return '[{0:+8.4e},{1:+8.4e},{2:+8.4e}]'.format(*xyz)

        def cmd_line_friendly2(clip_range):
            return '[{0:+8.4e},{1:+8.4e}]'.format(*clip_range)
        if interactor.GetKeySym() == 'c':
            print('\nPosition:    ' + cmd_line_friendly(camera.GetPosition()))
            print('FocalPoint:   ' + cmd_line_friendly(camera.GetFocalPoint()))
            print('ViewUp:       ' + cmd_line_friendly(camera.GetViewUp()))
            print('ClippingRange:' + cmd_line_friendly2(camera.GetClippingRange()))
            sys.stdout.write('\n--position ')
            sys.stdout.write(cmd_line_friendly(camera.GetPosition()))
            sys.stdout.write(' --focal-point ')
            sys.stdout.write(cmd_line_friendly(camera.GetFocalPoint()))
            sys.stdout.write(' --view-up ')
            sys.stdout.write(cmd_line_friendly(camera.GetViewUp()))
            sys.stdout.write(' --clipping-range ')
            sys.stdout.write(cmd_line_friendly2(camera.GetClippingRange()))
            sys.stdout.write('\n')
            sys.stdout.flush()

    render_window_interactor.AddObserver('KeyPressEvent', print_camera_position)

    if args.position:
        camera.SetPosition(args.position)
    if args.focal_point:
        camera.SetFocalPoint(args.focal_point)
    if args.view_up:
        camera.SetViewUp(args.view_up)
    if args.clipping_range:
        camera.SetClippingRange(args.clipping_range)
    if args.angle:
        camera.Roll(args.angle[0])
        camera.Elevation(args.angle[1])

    camera.Zoom(args.zoom)

    # re-render after setting camera
    render_window.Render()

    if args.png:
        window_to_image = vtk.vtkWindowToImageFilter()
        window_to_image.SetInput(render_window)
        #  window_to_image.SetMagnification(2)
        png_writer = vtk.vtkPNGWriter()
        png_writer.SetInputConnection(window_to_image.GetOutputPort())
        png_writer.SetFileName(args.png)
        png_writer.Write()

    if args.webgl:
        webgl_exporter = vtk.vtkPVWebGLExporter()
        webgl_exporter.SetFileName(args.webgl)
        webgl_exporter.SetRenderWindow(render_window)
        webgl_exporter.Update()

    if not args.png and not args.webgl:
        render_window_interactor.Start()


if __name__ == '__main__':
    main()
