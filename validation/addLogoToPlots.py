#!/usr/bin/env python3

"""
.. module:: addLogoToPlots
   :synopsis: Add the smodels logo to the pretty validation plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function
import glob,os,shutil
import tempfile

def addLogo(filename,logo = None ):
    """
    Add the logo image to the original plot.
    
    :param filename: path to the original plot (pdf or png)
    :param logo: path to the logo png image. If None, use default.
    """
    if not os.path.exists (filename ):
        print ( f"[addLogoToPlots] error cannot add watermark to non-existing file {filename}" )
        return


    if logo == None:
        if 'pdf' in filename:
            logo = 'smodels-bannerRotated.png'
        else:
            logo = 'smodels-banner.png'
    
    if '.pdf' in filename:
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfFileWriter, PdfFileReader
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
        watermark = PdfFileReader(open("watermark.pdf", "rb"))
        #Get the original file:
        input_file = PdfFileReader(open(filename, "rb"))
        # Create merged file
        output_file = PdfFileWriter()
        input_page = input_file.getPage(0)
        input_page.mergePage(watermark.getPage(0))
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

    elif '.png' in filename:
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
        layer.paste(mark, (0, layer.size[1]-50))
        #Merge original image and layer and save
        tmpF = tempfile.mktemp(suffix=".png",dir="./")
        Image.composite(layer, im, layer).save( tmpF )
        try:
            os.rename( tmpF, filename)
        except OSError as e:
            print ( f"[addLogoToPlots] could not rename {tmpF} to {filename}: {e}. Will try to move." )
            shutil.move ( tmpF, filename )
        
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
