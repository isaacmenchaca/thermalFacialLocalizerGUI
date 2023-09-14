import eel, json, os, cv2
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pandas as pd
import base64


eel.init('web')

@eel.expose
def onClickChooseFileButton():
    root = tk.Tk()
    root.attributes('-topmost', 1)
    root.withdraw()
    filePath = filedialog.askopenfilename()
    root.destroy()
    return filePath


# this function checks the data for how many thermal images there are.
# it will also automatically display the first image available or
# the last image whose data was saved in terms of localizations.
@eel.expose
def loadThermalInfo(filePath):
    print(filePath)
    

    thermalImages = np.load( filePath)/ 10 - 100
    thermalImages = thermalImages.reshape(-1, 288, 382)
    print('Thermal data file shape:', thermalImages.shape)
    numImages = thermalImages.shape[0]


    coordinatesFilePath = "/".join(filePath.split(".npy")[:-1]) + "_COORDINATES.csv"

    if not os.path.exists(coordinatesFilePath): 
        currentImage = 1

    else:
        data = pd.read_csv(coordinatesFilePath)
        currentImage = int(np.max(data["imageNumber"].values)) + 1


    img = prepareImage(thermalImages[currentImage - 1, :, :])
    eel.updateImageSrc(img)()

    return numImages, currentImage


def prepareImage(thermalImage):
    min_temp = np.min(thermalImage)
    max_temp = np.max(thermalImage)

    normalized_thermal_image = ((thermalImage - min_temp) / (max_temp - min_temp) * 255).astype(np.uint8)
    colorized_image = cv2.applyColorMap(normalized_thermal_image, cv2.COLORMAP_BONE)

    ret, png = cv2.imencode('.png', colorized_image)
    img = base64.b64encode(png)
    img = img.decode("utf-8")

    return img


@eel.expose
def saveCurrentProceedNextImage(filePath, currentImage, currentSavedCoordinates):
    coordinatesFilePath = "/".join(filePath.split(".npy")[:-1]) + "_COORDINATES.csv"

    if not os.path.exists(coordinatesFilePath): 
        print("creating new file")

        image_coord_dict = {"imageNumber": [currentImage]}

        for i, savedCoordinate in enumerate(currentSavedCoordinates):
            key = "landmark" + str(i + 1)
            image_coord_dict[key] = [str(savedCoordinate)]

        data = pd.DataFrame.from_dict(image_coord_dict)
        data.to_csv(coordinatesFilePath)

    else:

        columns = ["imageNumber"]

        for i in range(54):
            key = "landmark" + str(i + 1)
            columns.append(key)


        data = pd.read_csv(coordinatesFilePath)[columns]
        
        # going to have to check if the coordinate already exists.
        # if there is previous data on the image, then just replace values.
        if np.sum(np.isin(data["imageNumber"].values, currentImage)):
            for i, savedCoordinate in enumerate(currentSavedCoordinates):
                key = "landmark" + str(i + 1)
                data.loc[data["imageNumber"] == currentImage, key] = [str(savedCoordinate)]
            data.to_csv(coordinatesFilePath, mode='w')


        # otherwise, just add it in.
        else:
            image_coord_dict = {"imageNumber": [currentImage]}

            for i, savedCoordinate in enumerate(currentSavedCoordinates):
                key = "landmark" + str(i + 1)
                image_coord_dict[key] = [str(savedCoordinate)]
            
            newData = pd.DataFrame.from_dict(image_coord_dict)

            data = pd.concat([data, newData], ignore_index=True)
            data.to_csv(coordinatesFilePath, mode='w')

    print(data)

    # now increment currentImage
    currentImage += 1
    thermalImages = np.load( filePath)/ 10 - 100
    thermalImages = thermalImages.reshape(-1, 288, 382)

    img = prepareImage(thermalImages[currentImage - 1, :, :])
    eel.updateImageSrc(img)()

    return currentImage

@eel.expose
def checkNextExists(filePath, currentImage):
    coordinatesFilePath = "/".join(filePath.split(".npy")[:-1]) + "_COORDINATES.csv"
    
    columns = ["imageNumber"]
    for i in range(54):
        key = "landmark" + str(i + 1)
        columns.append(key)  

    data = pd.read_csv(coordinatesFilePath)[columns]
    
    exists = False
    if np.sum(np.isin(data["imageNumber"].values, currentImage)):
        exists = True

    return exists


@eel.expose
def goToPreviousImage(filePath, currentImage):
    coordinatesFilePath = "/".join(filePath.split(".npy")[:-1]) + "_COORDINATES.csv"
    
    columns = ["imageNumber"]
    for i in range(54):
        key = "landmark" + str(i + 1)
        columns.append(key)

    data = pd.read_csv(coordinatesFilePath)[columns]
    

    facialLocalizations = []
    for i in range(54):
        key = "landmark" + str(i + 1)
        feature = data[data["imageNumber"] == currentImage][key].values[0].strip('[]').split(',')
        feature = [int(value.strip()) for value in feature]
        facialLocalizations.append(feature)

    
    print(facialLocalizations)

    thermalImages = np.load( filePath)/ 10 - 100
    thermalImages = thermalImages.reshape(-1, 288, 382)

    img = prepareImage(thermalImages[currentImage - 1, :, :])
    eel.updateImageSrc(img)()

    return facialLocalizations


@eel.expose
def getCoordinates(filePath, currentImage):
    coordinatesFilePath = "/".join(filePath.split(".npy")[:-1]) + "_COORDINATES.csv"
    columns = ["imageNumber"]
    for i in range(54):
        key = "landmark" + str(i + 1)
        columns.append(key)

    data = pd.read_csv(coordinatesFilePath)[columns]


    
    facialLocalizations = []
    for i in range(54):
        key = "landmark" + str(i + 1)
        feature = data[data["imageNumber"] == currentImage][key].values[0].strip('[]').split(',')
        feature = [int(value.strip()) for value in feature]
        facialLocalizations.append(feature)

    return facialLocalizations



eel.start('index.html', size=(1000,750))            # Start (this blocks and enters loop)

 
