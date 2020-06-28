#!/usr/bin/env python3
import sys
import os
import re
import pathlib
import datetime
import pytz
from language_tags import tags
import secrets
from xml.dom import minidom
import argparse

# defaults safe to override when installing
xmllang = 'en-US'      # Must be valid BCP 47
booklang = 'en-US'     # Must be valid BCP 47
author = 'Book Author' # names should be upper case first letter
genre = 'Book Genre'
publisher = ''         # when empty, publisher metadata not added by default

# These default values probably do not need to be changed when installing
title = 'Book Title'
description = 'Book Description'
contentdir = 'EPUB'
opffile = 'content.opf'
pubdate = ''           # When set to empty string, it uses six weeks in future

# parameter related functions
def sanitizeTextString(stype, string):
    # convert < and >
    string = string.replace('<','&#x3c;')
    string = string.replace('>','&#x3e;')
    string = string.replace('&lt;','&#x3c;')
    string = string.replace('&gt;','&#x3e;')
    string = string.replace('&amp;','&#x26')
    # TODO - html5 named entities to hex
    # TODO - verify only numbered entities used
    # now replace hex/ordinal entities for <,>,&
    string = string.replace('&#x3c;','&lt;')
    string = string.replace('&#x3C;','&lt;')
    string = string.replace('&#x003c;','&lt;')
    string = string.replace('&#x003C;','&lt;')
    string = string.replace('&#60;','&lt;')
    string = string.replace('&#x3e;','&gt;')
    string = string.replace('&#x3E;','&gt;')
    string = string.replace('&#x003e;','&gt;')
    string = string.replace('&#x003E;','&gt;')
    string = string.replace('&#x26;','&amp;')
    string = string.replace('&#x0026;','&amp;')
    string = string.replace('&#38;','&amp;')
    # verify result can create a text node
    mydom = minidom.parseString('<whatever/>')
    try:
        mydom.createTextNode(string)
    except:
        print ('The parameter value entered for ' + stype + ' is not legal and can not be sanitized.')
        sys.exit(1)
    return string

def setBookTitle(string):
    string = sanitizeTextString('title', string)
    if len(string) == 0:
        print ('The book title can not be empty. Exiting.')
        sys.exit(1)
    global title
    title = string

def setBookDescription(string):
    string = sanitizeTextString('description', string)
    if len(string) == 0:
        print ('The book description can not be empty. Exiting.')
        sys.exit(1)
    global description
    description = string

def setBookGenre(string):
    string = sanitizeTextString('genre', string)
    if len(string) == 0:
        print('The book genre can not be empty. Exiting.')
        sys.exit(1)
    global genre
    genre = string

def setBookAuthor(string):
    string = sanitizeTextString('author', string)
    if len(string) == 0:
        print('The book author can not be empty. Exiting.')
        sys.exit(1)
    global author
    author = string

def setBookPublisher(string):
    string = sanitizeTextString('publisher', string)
    global publisher
    publisher = string

def setPublicationDate(string):
    import dateparser
    try:
        parsed = dateparser.parse(string)
    except:
        print ('I could not understand the publication date string. Exiting.')
        sys.exit(1)
    if parsed is None:
        print ('I could not understand the publication date string. Exiting.')
        sys.exit(1)
    global pubdate
    pubdate = parsed.strftime("%Y-%m-%d")

def setXmlLang(string):
    if not tags.check(string):
        print ('The specified XML language tag is not a BCP 47 language tag. Exiting.')
        sys.exit(1)
    global xmllang
    xmllang = string

def setBookLang(string):
    if not tags.check(string):
        print ('The specified book language tag is not a BCP 47 language tag. Exiting.')
        sys.exit(1)
    global booklang
    booklang = string

def setPackageDocumentFilename(string):
    # there is probably better way to do this
    test = re.sub('[\x30-\x39]', '', string)
    test = re.sub('[\x41-\x5a]', '', test)
    test = re.sub('[\x61-\x7a]', '', test)
    test = re.sub('[\x2d-\x2e]', '', test)
    test = re.sub('\x5f','', test)
    if not len(test) == 0:
        print ('The package document filename should only contain A-Za-z0-9_-. Exiting now.')
        sys.exit(1)
    if string[0] == '.':
        print ('The package document filename must not begin with a dot. Exiting now.')
        sys.exit(1)
    if string[0] == '_':
        print ('The package document filename should not begin with an underscore. Exiting now.')
        sys.exit(1)
    if string.count('.') > 1:
        print ('The package document filename should only contain one dot. Exiting now.')
        sys.exit(1)
    filename, extension = os.path.splitext(string)
    if len(extension) == 0:
        ext = '.opf'
    else:
        ext = extension.lower()
    if not ext == '.opf':
        print ('The package document filename should use a .opf extension. Exiting now.')
        sys.exit(1)
    if len(filename) > 28:
        print ('The package document filename should not exceed 32 characters. Exiting now.')
        sys.exit(1)
    if len(filename) == 0:
        print ('The package document filename can not be empty. Exiting now.')
        sys.exit(1)
    global opffile
    opffile = filename + ext

def setContentDirectory(string):
    # there is probably better way to do this
    test = re.sub('[\x30-\x39]', '', string)
    test = re.sub('[\x41-\x5a]', '', test)
    test = re.sub('[\x61-\x7a]', '', test)
    test = re.sub('[\x2d-\x2e]', '', test)
    test = re.sub('\x5f','', test)
    if not len(test) == 0:
        print ('The package content directory name should only contain A-Za-z0-9_-. Exiting now.')
        sys.exit(1)
    if string[0] == '.':
        print ('The package content directory name must not begin with a dot. Exiting now.')
        sys.exit(1)
    if string[0] == '_':
        print ('The package content directory name should not begin with an underscore. Exiting now.')
        sys.exit(1)
    if len(string) == 0:
        print ('The package content directory name can not be empty. Exiting now.')
        sys.exit(1)
    if len(string) > 32:
        print ('The package content directory name should not exceed 32 characters. Exiting now.')
        sys.exit(1)
    if string.count('..') > 0:
        print ('The package content directory name should not contain consecutive dots. Exiting now.')
        sys.exit(1)
    global contentdir
    contentdir = string

# non parameter related functions
def generatePubDate():
    pdate = pytz.utc.localize(datetime.datetime.utcnow() + datetime.timedelta(weeks=6))
    return pdate.strftime("%Y-%m-%d")

def getTime():
    now = pytz.utc.localize(datetime.datetime.utcnow())
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")

def prngUUID():
    rnd = secrets.token_hex(16)
    return(rnd[0:8] + "-" + rnd[8:12] + "-4" + rnd[13:16] + "-8" + rnd[17:20] + "-" + rnd[20:32])

def createContainerXML(xml, opf):
    mydom = minidom.parseString('<container/>')
    root = mydom.getElementsByTagName('container')[0]
    root.setAttribute('xmlns','urn:oasis:names:tc:opendocument:xmlns:container')
    root.setAttribute('version','1.0')
    rootfiles = mydom.createElement('rootfiles')
    root.appendChild(rootfiles)
    rootfile = mydom.createElement('rootfile')
    rootfile.setAttribute('full-path',opf)
    rootfile.setAttribute('media-type','application/oebps-package+xml')
    rootfiles.appendChild(rootfile)
    string = mydom.toprettyxml(indent="  ",newl="\n",encoding="UTF-8").decode()
    string = '\n'.join([x for x in string.split("\n") if x.strip()!=''])
    fh = open(xml, "w")
    fh.write(string)
    fh.close()

def createOPF(xml):
    mydom = minidom.parseString('<package/>')
    root = mydom.getElementsByTagName('package')[0]
    root.setAttribute('xml:lang', xmllang)
    root.setAttribute('xmlns', 'http://www.idpf.org/2007/opf')
    root.setAttribute('version', '3.0')
    metadata = mydom.createElement('metadata')
    metadata.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    root.appendChild(metadata)
    spacer = mydom.createTextNode('\n  ')
    manifest = mydom.createElement('manifest')
    manifest.appendChild(spacer)
    root.appendChild(manifest)
    spacer = mydom.createTextNode('\n  ')
    spine = mydom.createElement('spine')
    spine.appendChild(spacer)
    root.appendChild(spine)
    # add metadata
    text = mydom.createTextNode(title)
    node = mydom.createElement('dc:title')
    node.appendChild(text)
    metadata.appendChild(node)
    text = mydom.createTextNode(description)
    node = mydom.createElement('dc:description')
    node.appendChild(text)
    metadata.appendChild(node)
    text = mydom.createTextNode(genre)
    node = mydom.createElement('dc:type')
    node.appendChild(text)
    metadata.appendChild(node)
    text = mydom.createTextNode(booklang)
    node = mydom.createElement('dc:language')
    node.appendChild(text)
    metadata.appendChild(node)
    if not len(publisher) == 0:
        text = mydom.createTextNode(publisher)
        node = mydom.createElement('dc:publisher')
        node.appendChild(text)
        metadata.appendChild(node)
    if len(pubdate) == 0:
        text = mydom.createTextNode(generatePubDate())
    else:
        text = mydom.createTextNode(pubdate)
    node = mydom.createElement('dc:date')
    node.appendChild(text)
    metadata.appendChild(node)
    text = mydom.createTextNode(author)
    node = mydom.createElement('dc:creator')
    node.setAttribute('id', 'author0')
    node.appendChild(text)
    metadata.appendChild(node)
    text = mydom.createTextNode('aut')
    node = mydom.createElement('meta')
    node.setAttribute('property', 'role')
    node.setAttribute('refines', '#author0')
    node.setAttribute('scheme', 'marc:relators')
    node.appendChild(text)
    metadata.appendChild(node)
    # add uuid
    root.setAttribute('unique-identifier','prng-uuid')
    uuid = mydom.createTextNode(prngUUID())
    node = mydom.createElement('dc:identifier')
    node.appendChild(uuid)
    node.setAttribute('id','prng-uuid')
    metadata.appendChild(node)
    text = mydom.createTextNode('uuid')
    node = mydom.createElement('meta')
    node.appendChild(text)
    node.setAttribute('property', 'marc:scheme')
    node.setAttribute('refines', '#prng-uuid')
    metadata.appendChild(node)
    # add timestamp
    text = mydom.createTextNode(getTime())
    node = mydom.createElement('meta');
    node.setAttribute('property','dcterms:modified')
    node.appendChild(text)
    metadata.appendChild(node)
    # dump to file
    string = mydom.toprettyxml(indent="  ",newl="\n",encoding="UTF-8").decode()
    string = '\n'.join([x for x in string.split("\n") if x.strip()!=''])
    fh = open(xml, "w")
    fh.write(string)
    fh.close()
    if not xmllang == booklang:
        print ('Warning: The xml:lang ' + xmllang + ' differs from the book lang ' + booklang)
        print ('This might be okay but could be accidental.')

def setupContainer():
    metainf = pathlib.Path('META-INF')
    if metainf.exists():
        print ('META-INF already exists. Exiting now.')
        sys.exit(1)
    oebps = pathlib.Path(contentdir)
    if oebps.exists():
        print (contentdir + ' already exists. Exiting now.')
        sys.exit(1)
    mimetype = pathlib.Path('mimetype')
    if mimetype.exists():
        print ('mimetype file already exists. Exiting now.')
        sys.exit(1)
    metainf.mkdir()
    oebps.mkdir()
    with mimetype.open('w') as mt:
        mt.write('application/epub+zip')
    xmlpath = metainf.joinpath('container.xml')
    xml = xmlpath.resolve()
    createContainerXML(xml, contentdir + '/' + opffile)
    xmlpath = oebps.joinpath(opffile)
    xml = xmlpath.resolve()
    createOPF(xml)
    print ('Initial ePub complete. Be sure to check the data.')
    
def main():
    parser = argparse.ArgumentParser(description='Setup an initial ePub 3 container structure. All arguments are optional.')
    parser.add_argument('-t',
                    '--title',
                    action='store',
                    dest='title',
                    default=title,
                    help='The title of the book')
    parser.add_argument('-d',
                    '--description',
                    action='store',
                    dest='description',
                    default=description,
                    help='A short description of the book')
    parser.add_argument('-g',
                    '--genre',
                    action='store',
                    dest='genre',
                    default=genre,
                    help='The genre the book fits into')
    parser.add_argument('-a',
                    '--author',
                    action='store',
                    dest='author',
                    default=author,
                    help='The author of the book')
    parser.add_argument('-p',
                    '--publisher',
                    dest='publisher',
                    default=publisher,
                    help='The book publisher')
    parser.add_argument('-e',
                    '--pubdate',
                    dest='publicationdate',
                    default=pubdate,
                    help='Publication date')
    parser.add_argument('-x',
                    '--xmllang',
                    dest='xmllang',
                    default=xmllang,
                    help='BCP 47 language string for the Package Document File (OPF)')
    parser.add_argument('-l',
                    '--lang',
                    dest='booklang',
                    default=booklang,
                    help='BCP 47 language string for the language of the book')
    parser.add_argument('-D',
                    '--contentdir',
                    dest='oebps',
                    default=contentdir,
                    help='Content directory for your ePub files')
    parser.add_argument('-f',
                    '--opffile',
                    dest='opf',
                    default=opffile,
                    help='File name for the Package Document File (OPF)')

    args = parser.parse_args()
   
    setBookTitle(args.title.strip())
    setBookDescription(args.description.strip())
    setBookGenre(args.genre.strip())
    setBookAuthor(args.author.strip())
    string = args.publisher.strip()
    if len(string) > 0:
        setBookPublisher(string)
    string = args.publicationdate.strip()
    if len(string) > 0:
        setPublicationDate(string)
    setXmlLang(args.xmllang.strip())
    setBookLang(args.booklang.strip())
    setContentDirectory(args.oebps.strip())
    setPackageDocumentFilename(args.opf.strip())
    setupContainer()


if __name__ == "__main__":
    main() 
