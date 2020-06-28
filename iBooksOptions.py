#!/usr/bin/env python3
import sys
import os
import pathlib
from xml.dom import minidom
import argparse

def removeNodes(mydom, name):
    nodeList = mydom.getElementsByTagName('option')
    # in php removing node has to be done in reverse order or it changes the
    #  nodeList. I assume same is true with python minidom
    for node in reversed(nodeList):
        if node.hasAttribute('name') and node.getAttribute('name') == name:
            parent = node.parentNode
            parent.removeChild(node)

# All options with binary value default to false
#  if not present so only set to true
def addBinaryValueOption(mydom, parent, name):
    text = mydom.createTextNode('true')
    node = mydom.createElement('option')
    node.setAttribute('name', name)
    node.appendChild(text)
    parent.appendChild(node)

def boolArgs(string, param):
    string = string.lower()
    if string == 'none':
        return None
    elif string == 't':
        return True
    elif string == 'true':
        return True
    elif string == 'f':
        return False
    elif string == 'false':
        return False
    print ("Expecting True or False argument for " + param + ". Exiting now.")
    sys.exit(1)

def platformArg(string):
    string = string.lower()
    mylist = ['all', 'ipad', 'iphone']
    if string in mylist:
        return string
    print ("Platform must be all, ipad, or iphone. Exiting now.")
    sys.exit(1)

def orientArg(string):
    string = string.lower()
    if string == 'null':
        return None
    elif string == 'none':
        return 'none'
    elif string == 'portrait':
        return 'portrait-only'
    elif string == 'landscape':
        return 'landscape-only'
    print ("Expecting Portrait or Landscape or None for orientation-lock. Exiting now.")
    sys.exit(1)

def remOrientationFromGlobal(mydom,target):
    platformList = mydom.getElementsByTagName('platform')
    for platform in platformList:
        if platform.hasAttribute('name') and platform.getAttribute('name') == '*':
            optionList = platform.getElementsByTagName('option')
            for option in reversed(optionList):
                if option.hasAttribute('name') and option.getAttribute('name') == 'orientation-lock':
                    parent = option.parentNode
                    parent.removeChild(option)
    optionList = target.getElementsByTagName('option')
    for option in reversed(optionList):
        if option.hasAttribute('name') and option.getAttribute('name') == 'orientation-lock':
            target.removeChild(option)

def modifyMetaFile(xmlpath):
    if xmlpath.exists():
        with xmlpath.open('r') as xml:
            try:
                mydom = minidom.parse(xml)
            except:
                print ("Could not parse existing iBooks display options file. Exiting now.")
                sys.exit(1)
    else:
        mydom = minidom.parseString('<display_options/>')
    try:
        root = mydom.getElementsByTagName('display_options')[0]
    except:
        print ("Could not find root display_options node. Exiting now.")
    target = None
    platformlist = mydom.getElementsByTagName('platform')
    for platform in platformlist:
        if platform.hasAttribute('name'):
            name = platform.getAttribute('name')
            if name == '*' and pltf == 'all':
                target = platform
            elif name == pltf:
                target = platform
    # target may still be None
    if target is None:
        node = mydom.createElement('platform')
        if pltf == 'all':
            node.setAttribute('name','*')
        else:
            node.setAttribute('name', pltf)
        root.appendChild(node)
        target = node
    # we know the platform we need is defined and in the DOM
    if fxlay is not None:
        removeNodes(mydom, 'fixed-layout')
        if fxlay:
            addBinaryValueOption(mydom,target,'fixed-layout')
    if pubfont is not None:
        removeNodes(mydom, 'specified-fonts')
        if pubfont:
            addBinaryValueOption(mydom,target,'specified-fonts')
    if opspread is not None:
        removeNodes(mydom, 'open-to-spread')
        if opspread:
            addBinaryValueOption(mydom,target,'open-to-spread')
    if interactive is not None:
        removeNodes(mydom, 'interactive')
        if interactive:
            addBinaryValueOption(mydom,target,'interactive')
    if orientation is not None:
        if pltf == 'all':
            removeNodes(mydom, 'orientation-lock')
            if orientation != 'none':
                text = mydom.createTextNode(orientation)
                option = mydom.createElement('option')
                option.setAttribute('name', 'orientation-lock')
                option.appendChild(text)
                target.appendChild(option)
        else:
            remOrientationFromGlobal(mydom,target)
            if orientation != 'none':
                text = mydom.createTextNode(orientation)
                option = mydom.createElement('option')
                option.setAttribute('name', 'orientation-lock')
                option.appendChild(text)
                target.appendChild(option)
    # delete if no option nodes left in dom
    optionList = mydom.getElementsByTagName('option')
    if len(optionList) == 0:
        print ("No iBooks specific options.")
        if not xmlpath.exists():
            print ("Exiting now.")
            sys.exit(0)
        else:
            print ("iBooks specific file being deleted.")
            xmlpath.unlink()
            sys.exit(0)
    # delete platform nodes w/o child option nodes
    platformList = mydom.getElementsByTagName('platform')
    for platform in reversed(platformList):
        optionList = platform.getElementsByTagName('option')
        if len(optionList) == 0:
            root.removeChild(platform)
    # dump the DOM to file
    string = mydom.toprettyxml(indent="  ",newl="\n",encoding="UTF-8").decode()
    string = string.replace("?>", " standalone=\"yes\"?>")
    string = '\n'.join([x for x in string.split("\n") if x.strip()!=''])
    with xmlpath.open('w') as xml:
        xml.write(string)
    print ("META-INF file for iBooks options created.")

pltf = 'all'
fxlay = None
pubfont = None
opspread = None
interactive = None
orientation = None

def main():
    parser = argparse.ArgumentParser(description='Setup or modify iBooks custom META-INF XML file.')
    parser.add_argument('-p',
                    '--platform',
                    action='store',
                    dest='platform',
                    default='all',
                    help='The target iOS device platform')
    parser.add_argument('-l',
                    '--fixed-layout',
                    action='store',
                    dest='layout',
                    default='none',
                    help='True or False. Whether or not a fixed layout is being used')
    parser.add_argument('-f',
                    '--publisher-fonts',
                    action='store',
                    dest='fonts',
                    default='none',
                    help='True or False. Whether or not publisher fonts are embedded')
    parser.add_argument('-s',
                    '--open-to-spread',
                    action='store',
                    dest='spread',
                    default='none',
                    help='True or False. Whether or not the iBook should open to spread')
    parser.add_argument('-i',
                    '--interactive',
                    action='store',
                    dest='interactive',
                    default='none',
                    help='True or False. Whether or not scripted content exists')
    parser.add_argument('-o',
                    '--orientation-lock',
                    dest='orientation',
                    default='null',
                    help='Portrait or Landscape or None. A forced orientation for the ePub')
    parser.add_argument('-M',
                    '--META-INF',
                    action='store',
                    dest='metainf',
                    default='META-INF',
                    help='Path to META-INF directory.')
    args = parser.parse_args()

    global pltf
    global fxlay
    global pubfont
    global opspread
    global interactive
    global orientation
    pltf = platformArg(args.platform.strip())
    fxlay = boolArgs(args.layout.strip(), 'fixed-layout')
    pubfont = boolArgs(args.fonts.strip(), 'publisher-fonts')
    opspread = boolArgs(args.spread.strip(), 'open-to-spread')
    interactive = boolArgs(args.interactive.strip(), 'interactive')
    orientation = orientArg(args.orientation.strip())

    metainf = pathlib.Path(args.metainf.strip())
    if not metainf.resolve().parts[-1] == 'META-INF':
        print ('Expecting directory named META-INF. Exiting now.')
        sys.exit(1)
    if not metainf.exists():
        print ("The specified META-INF directory could not be found. Exiting now.")
        sys.exit(1)
    xmlpath = metainf.joinpath('com.apple.ibooks.display-options.xml')
    modifyMetaFile(xmlpath)

if __name__ == "__main__":
    main() 
