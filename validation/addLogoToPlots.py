#!/usr/bin/env python3

"""
.. module:: addLogoToPlots
   :synopsis: Add the smodels logo to the pretty validation plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

__all__ = [ "addLogo" ] ## is all you need

import glob,os,shutil
import tempfile
from typing import Union

def addLogo( filename : str, logo : Union[str,None] = None ):
    """
    Add the logo image to the original plot.
    
    :param filename: path to the original plot (pdf or png)
    :param logo: path to the logo png image. If None, use default.
    """
    if not os.path.exists (filename ):
        print ( f"[addLogoToPlots] error cannot add watermark to non-existing file {filename}" )
        return

    if '.pdf' in filename:
        addLogoToPdf ( filename, logo )

    elif '.png' in filename:
        addLogoToPng ( filename, logo )

def addLogoToPng ( filename : str, logo : Union[str,None] = None ):
    """ slap our logo onto a png file
    :param filename: path to the original plot (pdf or png)
    :param logo: path to the logo png image. If None, use default.
    """
    if logo == None:
        logo = 'smodels-transparent.png'
    from PIL import Image
    #Open original plot
    im = Image.open(filename)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')            
    #Open logo image
    mark = Image.open(logo)
    # Scale logo image:
    w = int(mark.size[0]*0.165)
    h = int(mark.size[1]*0.165)
    mark = mark.resize((w, h))
    
    #Create a new layer
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    #Copy logo to layer, 0,0 is upper left corner        
    # layer.paste(mark, (500,0))
    # layer.paste(mark, (0, 505))
    y =layer.size[1]
    if y > 550:
        y = y - 45
    else:
        y = y - 40
    layer.paste(mark, (0, y) )
    #Merge original image and layer and save
    tmpF = tempfile.mktemp(suffix=".png",dir="./")
    Image.composite(layer, im, layer).save( tmpF )
    try:
        os.rename( tmpF, filename)
    except OSError as e:
        print ( f"[addLogoToPlots] could not rename {tmpF} to {filename}: {e}. Will try to move." )
        shutil.move ( tmpF, filename )

def addLogoToPdf ( filename : str, logo : Union[str,None] = None ):
    """ slap our logo onto a pdf file
    :param filename: path to the original plot (pdf or png)
    :param logo: path to the logo png image. If None, use default.
    """
    if logo == None:
        logo = 'smodels-bannerRotated.png'
    from reportlab.pdfgen import canvas
    try:
        from PyPDF2 import PdfWriter, PdfReader
    except Exception as e: # old api
        from PyPDF2 import PdfFileWriter as PdfWriter
        from PyPDF2 import PdfFileReader as PdfReader
    # Create the watermark from an image
    if not os.path.exists ( "watermark.pdf" ):
        c = canvas.Canvas('watermark.pdf')
        #Draw logo watermark
        #x, y = 87, 645
        #x, y = 525, 30
        y, x = 380, 260
        c.drawImage(logo, y, x, width=35,height=80)
        c.save()            
    # Get the watermark file you just created
    watermark = PdfReader(open("watermark.pdf", "rb"))
    #Get the original file:
    input_file = PdfReader(open(filename, "rb"))
    # Create merged file
    output_file = PdfWriter()
    try:
        input_page = input_file.pages[0]
        wmpage = watermark.pages[0]
        input_page.merge_page(wmpage)
        # add page from input file to output document
        output_file.add_page(input_page)
    except Exception as e:
        input_page = input_file.getPage(0)
        wmpage = watermark.getPage(0)
        input_page.mergePage(wmpage)
        # add page from input file to output document
        output_file.addPage(input_page)
    # finally, write "output" to document-output.pdf
    tempF = tempfile.mktemp(suffix=".pdf", dir="./")
    with open( tempF, "wb") as outputStream:
        output_file.write(outputStream)
    try:
        os.rename( tempF, filename)
    except OSError as e:
        print ( f"[addLogoToPlots] could not rename {tempF} to {filename}: {e}. Will try to move." )
        shutil.move ( tempF, filename )
    #if os.path.exists ( "watermark.pdf" ):
    #    os.remove("watermark.pdf")
        
if __name__ == '__main__':
    addLogo( "tmp.pdf" )
    import sys; sys.exit()
    files = glob.glob('../../smodels-database/*/*/*/validation/*_pretty.*')
    if not files:
        print ( 'No files found' )
        
    for filename in files:
        if '_pretty.pdf' in filename:
            logo = 'smodels-bannerRotated.png'
            addLogo(filename,logo)
        elif '_pretty.png' in filename:
            logo = 'smodels-banner.png'
            addLogo(filename,logo)
        else:
            continue
        print ( "Adding logo to",filename )
        #print ( "Adding logo to",os.path.basename(filename) )
