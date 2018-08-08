#!/usr/bin/env python3

"""
.. module:: addLogoToPlots
   :synopsis: Add the smodels logo to the pretty validation plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function
import glob,os


def addLogo(filename,logo):
    """
    Add the logo image to the original plot.
    
    :param filename: path to the original plot (pdf or png)
    :param logo: path to the logo png image
    """
    
    if '.pdf' in filename:
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfFileWriter, PdfFileReader
        # Create the watermark from an image
        c = canvas.Canvas('watermark.pdf')
        #Draw logo watermark
        c.drawImage(logo, 87, 645, width=35,height=80)
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
        with open('temp_test_logo.pdf', "wb") as outputStream:
            output_file.write(outputStream)
            
        os.remove("watermark.pdf")
        os.rename('temp_test_logo.pdf', filename)

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
        #Copy logo to layer            
        layer.paste(mark, (546, 96))
        #Merge original image and layer and save
        Image.composite(layer, im, layer).save('temp_test_logo.png')
        os.rename('temp_test_logo.png', filename)
        
if __name__ == '__main__':
    
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
        print ( "Adding logo to",os.path.basename(filename) )
