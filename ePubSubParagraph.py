#!/usr/bin/env python3
import sys
import os
import re
import tempfile
from zipfile import ZipFile
from xml.dom import minidom

# Copyright 2020 Michael A. Peters but released to the equivalent of public domain:
#
# Creative Commons CC0 “No Rights Reserved”
#  See https://creativecommons.org/share-your-work/public-domain/cc0/
#
# Proof of concept use only, the specialCases() function no doubt needs stuff added.

# boolean so no archive is created if no subparagraphs are implemented
modifiedFiles = False

# The fact that this is necessary indicates that minidom is not the right tool for this.
# That or I am not using minidom correctly
def specialCases(string):
    # fix broken time tag whitespace
    string = re.sub('\s+<time', ' <time', string)
    string = re.sub('</time>\s+,', '</time>,', string)
    string = re.sub('</time>\s+.', '</time>.', string)
    return string

def showUsage():
    print ("Usage: " + sys.argv[0] + " path/to/input.epub " + " path/to/output.epub")
    sys.exit(1)

# deep clones a node and adds clone as child to div
def cloneDomNode(node, div):
    clone = node.cloneNode(True)
    div.appendChild(clone)

# creates a flagged subparagraph (node var) as paragraph and adds to div
def cloneToParagraph(mydom, node, div, pstyle, pclass):
    par = mydom.createElement('p')
    if len(pstyle) > 0:
        par.setAttribute('style', pstyle)
    if len(pclass) > 0:
        par.setAttribute('class', pclass)
    for child in node.childNodes:
        clone = child.cloneNode(True)
        par.appendChild(clone)
    div.appendChild(par)

# parses an XHTML file and if subparagraphs found, modifies the file.
def adjustParagraphNodes(xhtmlfile):
    global modifiedFiles
    try:
        mydom = minidom.parse(xhtmlfile)
    except:
        print ("Could not parse " + xhtmlfile + " as XML. Skipping.")
        return()
    domchanged = False
    # get list of all paragraph nodes
    nodelist = mydom.getElementsByTagName('p')
    # walk nodelist backwards as it will be changing
    i = len(nodelist) - 1
    while i >= 0 :
        counter = 0
        node = nodelist[i]
        newdiv = mydom.createElement('div')
        divid = ''
        pstyle = ''
        pclass = ''
        if node.hasAttribute('id'):
            divid = node.getAttribute('id')
        if node.hasAttribute('style'):
            pstyle = node.getAttribute('style')
        if node.hasAttribute('class'):
            pclass = node.getAttribute('class')
        for child in node.childNodes:
            subpar = False
            if child.nodeType == 1 and child.tagName == "span":
                # change this to epub:type if/when official
                if child.hasAttribute('data-epubtype') and child.getAttribute('data-epubtype') == 'subparagraph':
                    subpar = True
                    counter += 1
            if subpar:
                cloneToParagraph(mydom, child, newdiv, pstyle, pclass)
            else:
                cloneDomNode(child, newdiv)
        # only act if counted more than one subparagraph
        if counter > 1:
            node.parentNode.replaceChild(newdiv, node)
            domchanged = True
            if len(divid) > 0:
                newdiv.setAttribute('id', divid)
        # reduce iterator by 1
        i -= 1
    if domchanged:
        #overwrite original file
        string = mydom.toprettyxml(indent="  ",newl="\n",encoding="UTF-8").decode()
        string = '\n'.join([x for x in string.split("\n") if x.strip()!=''])
        # special cases
        string = specialCases(string)
        try:
            f = open(xhtmlfile, 'w')
        except:
            print("Could not open " + xhtmlfile + " for writing. Exiting.")
            sys.exit(1)
        f.write(string)
        f.close
        modifiedFiles = True
        print ("File " + xhtmlfile + " has been modified.")

# create new zip archive with files in same order as original
def createModifiedEpub(unzipdir, outputfile, namelist):
    with ZipFile(outputfile, 'w') as newEpub:
        for elem in namelist:
            filename = os.path.join(unzipdir, elem)
            newEpub.write(filename,elem)

# The proper way would probably be to read the OPF file and extract all
#  the files with a application/xml+xhtml mime type but those files
#  really should be .xhtml extension anyway.
def adjustEpub(inputfile, outputfile):
    with tempfile.TemporaryDirectory() as unzipdir:
        with ZipFile(inputfile, 'r') as myzip:
            namelist = myzip.namelist()
            myzip.extractall(unzipdir)
            for path,dirs,files in os.walk(unzipdir):
                for filename in files:
                    if filename.endswith(".xhtml"):
                        adjustParagraphNodes(os.path.join(path,filename))
        if modifiedFiles:
            createModifiedEpub(unzipdir, outputfile, namelist)
            print("Modified ePub " + outputfile + " has been created.")
            print("Please validate with ePubCheck.")
        else:
            print("Subparagraph notation not found. Exiting.")

def main():
    if len(sys.argv) != 3:
        showUsage()
    adjustEpub(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()