import xml.etree.ElementTree as et

filehandler = open("encyclopaedia-britannica-sample/144133901/144133901-mets.xml","r")
raw_data = et.parse(filehandler)
data_root = raw_data.getroot()
filehandler.close()

for children in data_root:
    for child in children:
        print(child.tag, child.text, children.tag, children.text)