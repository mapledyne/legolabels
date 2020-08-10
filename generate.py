
from PIL import Image, ImageDraw
from image_utils import ImageText
import webcolors
import requests
import json
import ast
import tempfile
import shutil
import re
import sys

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'


def downloadFile(url, file_name):
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        headers = {
            'User-Agent': user_agent
        }
        response = requests.get(url, headers=headers)
        # write to file
        file.write(response.content)


def downloadText(url):
    # get request
    headers = {
        'User-Agent': user_agent
    }
    response = requests.get(url, headers=headers)
    return response.content.decode("utf-8")


def createImage(w, h, partImg):
    global tmpdirpath
    img = Image.open(partImg, 'r')
    global img_w, img_h
    img_w, img_h = img.size
    pad_h = h // 7
    # background = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    background = ImageText((w, h), background=(255, 255, 255, 255))
    bg_w, bg_h = background.image.size
    offset = ((bg_w - img_w) // 2, pad_h)
    background.image.paste(img, offset)
    return background


def addFirstQuote(string):
    retval = ""
    first = True
    for ch in string:
        if (first):
            if (ch == "\t" or ch == " " or ch == ","):
                retval += ch
            else:
                retval += '"' + ch
                first = False
        else:
            retval += ch
    return retval


def getInfo(html):
    body = ""
    started = False
    startLine = "var_var_item={"
    endLine = "};"
    for line in html.splitlines():
        lineNoSpaces = line.replace("\t", "")
        lineNoSpaces = lineNoSpaces.replace(" ", "")
        if (started):
            if (lineNoSpaces == endLine):
                return json.loads("{" + body + "}")
            jsonLine = line.replace("'", '"')
            jsonLine = jsonLine.replace(":", '":', 1)
            jsonLine = addFirstQuote(jsonLine)
            body += jsonLine
        else:
            if (lineNoSpaces == startLine):
                started = True


def getNamePartsReg(line, reg):
    matchObj = re.match(reg, line, re.M | re.I)

    if matchObj:
        return (matchObj.group(1), matchObj.group(2), matchObj.group(3))
    return None


def getNameParts(line):
    parts = getNamePartsReg(line, r'(.*)([0-9]+ x [0-9]+ x [0-9]+)(.*)')
    if (parts is None):
        parts = getNamePartsReg(line, r'(.*)([0-9]+ x [0-9]+)(.*)')
        if (parts is None):
            parts = (line, "", "")
    return parts


def parse_colour(s, alpha=255):
    r = 0
    g = 0
    b = 0
    if isinstance(s, tuple):
        try:
            r = s[0]
            g = s[1]
            b = s[2]
        except Error:
            pass
        return (r, g, b, alpha)

    s = s.lower()
    try:
        r, g, b = webcolors.name_to_rgb(s)
    except ValueError:
        try:
            r, g, b = webcolors.hex_to_rgb(s)
        except ValueError:
            pass
    return (r, g, b, alpha)


def main(outputFile, partNum, w, h, colours, translucent, cmdLine):
    # download info about the part
    infoUrl = "https://www.bricklink.com/v2/catalog/catalogitem.page?P=" + partNum
    infoHTML = downloadText(infoUrl)
    info = getInfo(infoHTML)
    global tmpdirpath
    # find the picture url
    # imgUrl = "https:"+info["strMainLImgUrl"]
    imgUrl = "https://img.bricklink.com/ItemImage/PN/86/" + partNum + ".png"
    itemName = info["strItemName"]
    itemFullType, itemSize, itemDesc = getNameParts(itemName)
    itemSplit = itemFullType.split(",", 1)
    itemSize = itemSize.replace(" ", "")
    if (len(itemSplit) > 0):
        itemType = itemSplit[0]
    else:
        itemType = ""
    if (len(itemSplit) > 1):
        itemSubType = itemSplit[1]
    else:
        itemSubType = ""

    try:
        imageFile = cmdLine["-itemImageFile"]
    except:
        imageFile = tmpdirpath + "img.png"
        # download the image
        downloadFile(imgUrl, imageFile)
    img = createImage(w, h, imageFile)

    dims = itemSize.split("x")
    largestDim = 0
    fontSize = 30
    try:
        for dim in dims:
            dimInt = int(dim.strip())
            if (dimInt > largestDim):
                largestDim = dimInt
    except ValueError:
        pass

    # check if any text is explicitly given
    try:
        itemType = cmdLine["-itemType"]
    except:
        pass
    try:
        itemSubType = cmdLine["-itemSubType"]
    except:
        pass
    try:
        largestDim = cmdLine["-itemLength"]
    except:
        pass
    try:
        itemSize = cmdLine["-itemSize"]
    except:
        pass
    try:
        itemDesc = cmdLine["-itemDescription"]
    except:
        pass
    try:
        partNum = cmdLine["-itemPartNum"]
    except:
        pass

    colour = (50, 50, 50)
    global scriptPath
#    font = scriptPath + '/GillSansMT.ttf'
    font = scriptPath + '/Bubblegum.ttf'
    try:
        font = cmdLine["-fontFile"]
    except:
        pass

    padding = h // 11  # 30
    x = padding
    y = -padding
    biggestY = img_h + padding
    spaceLeft = (w / 2) - (img_w / 2) - padding
    # draw the piece type top left
    tx, th = img.write_text_box((x, y),
                                itemType,
                                box_width=spaceLeft,
                                font_filename=font,
                                font_size=int(fontSize * 1.5),
                                color=colour)
    y += th + padding
    # put the subtype below that
    tx, th = img.write_text_box((x, y),
                                itemSubType,
                                box_width=spaceLeft,
                                font_filename=font,
                                font_size=int(fontSize),
                                color=colour)
    y += th + padding

    # if we have a size, draw the largest dimension really big

    # if (largestDim > 0):
    #     tx, th = img.write_text_box((x, y),str(largestDim),box_width=spaceLeft, font_filename=font, font_size=(fontSize*3), color=(192, 192, 192))
    #     y += th
    # if (y > biggestY):
    #     biggestY = y

    x = w - (spaceLeft + padding)
    y = -padding
    # on the right draw the size
    # tx, th = img.write_text_box((x, y),itemSize,box_width=spaceLeft, font_filename=font, font_size=int(fontSize*1.5), color=colour, place="right")
    tx, th = img.write_text_box((x - img_w, y),
                                itemSize,
                                box_width=(spaceLeft + img_w),
                                font_filename=font,
                                font_size=int(fontSize * 1.5),
                                color=colour,
                                place="right")
    y += th + padding
    # and the description below that
    tx, th = img.write_text_box((x, y),
                                itemDesc,
                                box_width=spaceLeft,
                                font_filename=font,
                                font_size=fontSize,
                                color=colour,
                                place="right")
    y += th + (h // 7) # 50
    # and the part number below that
    tx, th = img.write_text_box((x, y),
                                partNum,
                                box_width=spaceLeft,
                                font_filename=font,
                                font_size=fontSize,
                                color=colour,
                                place="right")
    y += th
    # then at the bottom of the image draw the colours

    color_height = h // 7 #  50

    if (y > biggestY):
        biggestY = y
    fillColour = (255, 0, 0, 128)
    outlineColour = (0, 0, 0, 255)
    rectangle = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(rectangle)
    # biggestY += 100
    # if (biggestY > h - 60):
    #     biggestY = h - 60
    biggestY = h - color_height - padding
    alpha = 255
    fromX = 20
    toX = w - 20
    if (translucent):
        alpha = 128

    thisFromX = fromX
    thisWidth = (toX - fromX) / len(colours)
    draw.rectangle([(0, 0), (w - 1, h - 1)], fill=None, outline=(0, 0, 0, 255))
    for colour in colours:
        thisToX = thisFromX + thisWidth
        col = parse_colour(colour, alpha)
        draw.rectangle([(thisFromX, biggestY),
                        (thisToX, biggestY + color_height)],
                       fill=col,
                       outline=None)
        thisFromX += thisWidth
    if (translucent):
        draw.rectangle([(fromX, biggestY),
                        (toX, biggestY + color_height)],
                       fill=None,
                       outline=(0, 0, 0, 255))
    img.image = Image.alpha_composite(img.image, rectangle)

    img.save(outputFile)


tmpdirpath = tempfile.mkdtemp() + "/"

# Default with /height from:
# Assuming px/in for printing = 200
# 4" x 1.69" for default label
# (Smaller label should be 3" x 1")
# Width = 200 * 4
# Height = 200 * 1.69

scriptPath = sys.path[0]
argName = "scriptName"
cmdLine = {"-translucent": False,
           "-width": 800,
           "-height": 338,
           "-colours": "rainbow"}

for arg in sys.argv:
    if (argName != ""):
        cmdLine[argName] = arg
        argName = ""
    else:
        if (arg == "-translucent"):
            cmdLine[arg] = True
        else:
            argName = arg

try:
    partNum = cmdLine["-partNum"]
except:
    print("Part number must be specified")
    print("")
    print("Usage:")
    print(sys.argv[0]+" -partNum <partNum> [-translucent] [-colours <colours>] [-o <outputPngFile>] [-width <pixels>] [-height <pixels>] [-itemType <string>] [-itemSubType <string>] [-itemLength <string>] [-itemSize <string>] [-itemDescription <string>] [-itemPartNum <string>] [-itemImageFile <filename>] [-fontFile <filename>]")
    exit(-1)

try:
    outputFile = cmdLine["-o"]
except:
    outputFile = partNum + " - " + cmdLine["-colours"] + ".png"

try:
    cmdLine["-colours"] = cmdLine["-colors"]
except:
    pass

if cmdLine["-colours"].lower() == "rainbow":
    colours = []
    # fade from black to white
    for i in range(0, 255, 15):
        colours.append((i, i, i))
    # to blue
    for i in range(255, 0, -15):
        colours.append((i, i, 255))
    # to cyan
    for i in range(0, 255, 15):
        colours.append((0, i, 255))
    # to green
    for i in range(255, 0, -15):
        colours.append((0, 255, i))
    # to yellow
    for i in range(0, 255, 15):
        colours.append((i, 255, 0))
    # to red
    for i in range(255, 0, -15):
        colours.append((255, i, 0))
else:
    colours = cmdLine["-colours"].split()
translucent = cmdLine["-translucent"]
width = int(cmdLine["-width"])
height = int(cmdLine["-height"])
main(outputFile, partNum, width, height, colours, translucent, cmdLine)

shutil.rmtree(tmpdirpath)
