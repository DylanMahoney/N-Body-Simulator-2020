import pygame
import time
import random
import numpy
import math
from datetime import datetime
import csv

#Creating and opening file that will store data produced by simulation
filename = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")+".csv"
file = open(filename,"w")

#Defining different colors
BLACK = (0,0,0)
DARK_BLUE = (0,0,128)
BLUE = (0,0,255)
DARK_GREEN = (0,128,0)
DARK_CYAN = (0,128,128)
SKY_BLUE = (0,128,255)
GREEN = (0,255,0)
PASTEL_GREEN = (0,255,128)
CYAN = (0,255,255)
MAROON = (128,0,0)
PURPLE = (128,0,128)
ROYAL_PURPLE = (128,0,255)
DIRTY_YELLOW = (128,128,0)
GRAY = (128,128,128)
PASTEL_PURPLE = (128,128,255)
LIME_GREEN = (128,255,0)
PALE_GREEN = (128,255,128)
PASTEL_BLUE = (128,255,255)
RED = (255,0,0)
BRIGHT_PINK = (255,0,128)
MAGENTA = (255,0,255)
ORANGE = (255,128,0)
PEACH = (255,128,128)
PASTEL_PINK = (255,128,255)
YELLOW = (255,255,0)
CREAM = (255,255,128)
WHITE = (255,255,255)

#kilogram meter second units used throughout
G = 6.674*(10**-11)
DISTANCE_SCALE = 10**5 #meters per pixel
RADIUS_SCALE = 10**7 #if it were to scale the planets would be too small to see (also meters per pixel)
TIME_SCALE = 10**6 #seconds per frame
INIT_TIME_SCALE = TIME_SCALE #Later used while adjusting time scale
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

#Initializing pygame and creating fonts to be used later
pygame.init()
font = pygame.font.Font('freesansbold.ttf',10)
fpsfont = pygame.font.Font('freesansbold.ttf',20)

#the vector outputted points from point2 to point1
def diffTwoPoints(point1,point2):
    xDiff = point1[0]-point2[0]
    yDiff = point1[1]-point2[1]
    return numpy.array([xDiff,yDiff])

#Gives distance between two points
def distTwoPoints(point1,point2):
    return numpy.linalg.norm(diffTwoPoints(point1,point2))

#Gets user input of very large or very small numbers using scientific notation
#Message explains what value that program is asking for
def getSciNotation(message):
    print(message)
    invalid = True
    while invalid:
        orderedPair = input("Enter an ordered pair \"a,b\" for the number a*10^b: ").split(',')
        try:
            orderedPair = tuple(orderedPair)
            orderedPair = (float(orderedPair[0]),float(orderedPair[1]))
            if len(orderedPair) == 2:
                answer = orderedPair[0] * 10**(orderedPair[1])
                if not math.isinf(answer): #Very large numbers could be rounded to infinity, which would be bad
                    invalid = False
                    return answer
        except:
            pass
#This function takes the current time and the positions and velocities of all the heavenly bodies and saves them to the file created and opened earlier in a new line using csv
def saveData(time,bodies,file):
    line = ""
    line += str(time)+"," #records time
    for body in bodies:
        line += str(body.getPosition()[0]) + ","
        line += str(body.getPosition()[1]) + ","
        line += str(body.getVelocity()[0]) + ","
        line += str(body.getVelocity()[1]) + ","
    line += "\n"
    file.write(line)

class Body:
    def __init__(self,name,color,position,velocity,mass,radius):
        self.color = color
        self.position = numpy.array(position)
        self.velocity = numpy.array(velocity)
        self.mass = mass
        self.radius = radius
        self.energyPerMass = 0
        self.name = name
        #pastPositions is a record of where the body has been, but with positions rounded to the nearest pixel (using the DISTANCE_SCALE). A new position is only added to pastPositions
        #if it is in a different pixel. The advantage of having a list of rounded positions instead of a list of pixels is that if the DISTANCE_SCALE changes (from a body going off screen), pastPositions can be
        #used to accurately draw the body's path with the new DISTANCE_SCALE, something which would be harder if pixels were stored directly.
        self.pastPositions = []
        #As mentioned above, a new position is only added to pastPositions if that position is in a different pixel. The pixels which the body has already covered are stored in pixelsAlreadyCovered so that
        #a new position can be added to pastPositions only when that position is in a different pixel.
        self.pixelsAlreadyCovered = []
        self.nameTag = font.render(self.name,True,self.color,(0,0,0)) # to display the name of the body
        self.nameRect = self.nameTag.get_rect()
        self.nameRect.center = (int(self.position[0]/DISTANCE_SCALE),int(self.position[1]/DISTANCE_SCALE)-10)

    def getPosition(self):
        return self.position

    def setPosition(self,position):
        self.position = position

    def getVelocity(self):
        return self.velocity

    def setVelocity(self,velocity):
        self.velocity = velocity

    def getMass(self):
        return self.mass

    def getRadius(self):
        return self.radius

#Later, mechanical energy per mass is used to adjust the speeds of the different bodies in accordance with conservation of energy
    def getEnergyPerMass(self):
        return self.energyPerMass

    def setEnergyPerMass(self,energyPerMass):
        self.energyPerMass = energyPerMass

    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name

#Finds the gravitational potential energy of the body divided by its mass
    def findGPEPerMass(self,bodies):
        answer = 0
        for otherbody in bodies:
            if not distTwoPoints(self.position,otherbody.getPosition()) == 0:
                distance = distTwoPoints(self.position,otherbody.getPosition())
                answer -= G*otherbody.getMass()/distance #GPE equation based on Newton's Law of Universal Gravitation
        return answer

    def findEnergyPerMass(self,bodies):
        answer = 0
        answer += 0.5*numpy.linalg.norm(self.getVelocity())**2
        answer += self.findGPEPerMass(bodies)
        #This summed up the GPE divided by the mass and the kinetic energy divided by the mass
        return answer
    
    def drawBody(self,screen):
        #When drawing the bodies, SCREEN_WIDTH/2 and SCREEN_HEIGHT/2 are added to the pixel values. This is because
        #(0,0) in pygame refers to the top left of the screen (positive y direction is down), so adding those values
        #moves the origin used by the position variables to the center of the screen
        x = int(self.position[0]/DISTANCE_SCALE+SCREEN_WIDTH/2)
        y = int(self.position[1]/DISTANCE_SCALE+SCREEN_HEIGHT/2)
        pygame.draw.circle(screen,self.color,(x,y),int(self.radius/RADIUS_SCALE))

    def calculateAcceleration(self,bodies):
        acceleration = numpy.array([0,0])
        for body in bodies:
            if not distTwoPoints(self.position,body.getPosition()) == 0: #Doesn't calculate gravitational attraction on body from itself
                #Newton's Law of Universal Gravitation combined with his Second Law
                distance = distTwoPoints(self.position,body.getPosition())
                r_vector = diffTwoPoints(body.getPosition(),self.position)
                accelContribution = numpy.multiply(G*body.getMass()/(distance**3),r_vector)
                acceleration = acceleration + accelContribution #sums up contributions from all the bodies
        return acceleration

    #This function adds the body's position (having been rounded to the nearest pixel) to the pastPositions list and adds the pixel covered to pixelsAlreadyCovered, but only if the pixel hasn't already been covered
    def recordPosition(self):
        roundedPosition = numpy.array([DISTANCE_SCALE*int(self.position[0]/(DISTANCE_SCALE)),DISTANCE_SCALE*int(self.position[1]/(DISTANCE_SCALE))])
        pixelCovered = (int(self.position[0]/DISTANCE_SCALE),int(self.position[1]/DISTANCE_SCALE))
        if not pixelCovered in self.pixelsAlreadyCovered:
            self.pastPositions.append(roundedPosition)
            self.pixelsAlreadyCovered.append(pixelCovered)

    #This function is used when the DISTANCE_SCALE changes. A pixel which was once covered by the body's path may no longer be covered
    def clearPixelsAlreadyCovered(self):
        self.pixelsAlreadyCovered = []

    #uses pastPositions to draw the path of the body on the screen
    def drawPath(self,screen):
        for point in self.pastPositions:
            x = int(point[0]/DISTANCE_SCALE+SCREEN_WIDTH/2)
            y = int(point[1]/DISTANCE_SCALE+SCREEN_HEIGHT/2)
            pygame.draw.circle(screen,self.color,(x,y),1)

    #animates the names of the bodies displayed on screen
    def drawName(self,screen):
        self.nameRect.center = (int(self.position[0]/DISTANCE_SCALE+SCREEN_WIDTH/2),int(self.position[1]/DISTANCE_SCALE-10+SCREEN_HEIGHT/2))
        screen.blit(self.nameTag,self.nameRect)

#This section of code is how the user determines the number of bodies and the properties of each
addingBodies = True
bodies = [] #creates the bodies list, which is where all of the bodies are stored
print("Welcome to the n-body simulator!")
print("All data should be inputted and will be stored in m/k/s units :)")
print("The positive x direction is rightward, and the positive y direction is downward.")
print("The first body added to the system will start at the center of the screen.")
while addingBodies: #while loop runs until the user says to stop adding more bodies to the system
    continuing = input("Would you like to add a body to the system? (yes or no): ")
    if continuing == "no":
        addingBodies = False
    if continuing == "yes":
        name = str(input("Name (The names \"Sun\", \"Mercury\", \"Venus\", \"Earth\", \"Mars\", \"Jupiter\", \"Saturn\", \"Uranus\", or \"Neptune\" will automatically fill in the masses and radii of those bodies): "))
        validColorMode = False
        while not validColorMode: #While loop that gets which metho the user would like to use to enter a color and acts on the user's choice
            colorMode = input("Would you like to use a color word or an RGB value? (word or rgb): ")
            if colorMode == "word":
                validColorMode = True
                validColor = False
                while not validColor: #While loop that gets the name of a color coded into the system from the user
                    color = input("What color? (BLACK, DARK_BLUE, BLUE, DARK_GREEN, DARK_CYAN, SKY_BLUE, GREEN, PASTEL_GREEN, CYAN, MAROON, PURPLE, ROYAL_PURPLE, DIRTY_YELLOW, GRAY, PASTEL_PURPLE, LIME_GREEN, PALE_GREEN, PASTEL_BLUE, RED, BRIGHT_PINK, MAGENTA, ORANGE, PEACH, PASTEL_PINK, YELLOW, CREAM, or WHITE): ")
                    if color == "BLACK":
                        color = BLACK
                        validColor = True
                    if color == "DARK_BLUE":
                        color = DARK_BLUE
                        validColor = True
                    if color == "BLUE":
                        color = BLUE
                        validColor = True
                    if color == "DARK_GREEN":
                        color = DARK_GREEN
                        validColor = True
                    if color == "DARK_CYAN":
                        color = DARK_CYAN
                        validColor = True
                    if color == "SKY_BLUE":
                        color = SKY_BLUE
                        validColor = True
                    if color == "GREEN":
                        color = GREEN
                        validColor = True
                    if color == "PASTEL_GREEN":
                        color = PASTEL_GREEN
                        validColor = True
                    if color == "CYAN":
                        color = CYAN
                        validColor = True
                    if color == "MAROON":
                        color = MAROON
                        validColor = True
                    if color == "PURPLE":
                        color = PURPLE
                        validColor = True
                    if color == "ROYAL_PURPLE":
                        color = ROYAL_PURPLE
                        validColor = True
                    if color == "DIRTY_YELLOW":
                        color = DIRTY_YELLOW
                        validColor = True
                    if color == "GRAY":
                        color = GRAY
                        validColor = True
                    if color == "PASTEL_PURPLE":
                        color = PASTEL_PURPLE
                        validColor = True
                    if color == "LIME_GREEN":
                        color = LIME_GREEN
                        validColor = True
                    if color == "PALE_GREEN":
                        color = PALE_GREEN
                        validColor = True
                    if color == "PASTEL_BLUE":
                        color = PASTEL_BLUE
                        validColor = True
                    if color == "RED":
                        color = RED
                        validColor = True
                    if color == "BRIGHT_PINK":
                        color = BRIGHT_PINK
                        validColor = True
                    if color == "MAGENTA":
                        color = MAGENTA
                        validColor = True
                    if color == "ORANGE":
                        color = ORANGE
                        validColor = True
                    if color == "PEACH":
                        color = PEACH
                        validColor = True
                    if color == "PASTEL_PINK":
                        color = PASTEL_PINK
                        validColor = True
                    if color == "YELLOW":
                        color = YELLOW
                        validColor = True
                    if color == "CREAM":
                        color = CREAM
                        validColor = True
                    if color == "WHITE":
                        color = WHITE
                        validColor = True
            if colorMode == "rgb":
                validColorMode = True
                validColor = False
                while not validColor: #loop that gets a valid RGB triple from the user
                    color = tuple(input("What color? (input as a tuple, e.g. (234,156,83): "))
                    if color[0] >= 0 and color[0] <= 255 and color[1] >= 0 and color[1] <= 255 and color[2] >= 0 and color[2] <= 255:
                        validColor = True
        if len(bodies) == 0: #Sets the first body the user entered to have position [0,0]
            position = [0,0]
        #gets position of body from  user
        else:
            position = [getSciNotation("Input initial x position of the body (relative to first body)"),getSciNotation("Input initial y position of the body (relative to first body)")]
        velocity = [getSciNotation("Input initial x velocity of the body"),getSciNotation("Input initial y velocity of the body")] #gets velocity from user
        #The following lines set the mass and radius of the body if the user used one of the reserved words from bodies in our solar system
        if name == "Sun":
            mass = 1.989*(10**30)
            radius = 696.34*(10**6)
        elif name == "Mercury":
            mass = 3.285*(10**23)
            radius = 2.4397*(10**6)
        elif name == "Venus":
            mass = 4.867*(10**24)
            radius = 6.0518*(10**6)
        elif name == "Earth":
            mass = 5.972*(10**24)
            radius = 6.371*(10**6)
        elif name == "Mars":
            mass = 6.39*(10**23)
            radius = 3.3895*(10**6)
        elif name == "Jupiter":
            mass = 1.898*(10**27)
            radius = 69.911*(10**6)
        elif name == "Saturn":
            mass = 5.683*(10**26)
            radius = 58.232*(10**6)
        elif name == "Uranus":
            mass = 8.681*(10**25)
            radius = 25.362*(10**6)
        elif name == "Neptune":
            mass = 1.024*(10**26)
            radius = 24.622*(10**6)
        #If the user didn't used a reserved word, this gets the mass and radius from the user
        else:
            mass = getSciNotation("Mass: ")
            radius = getSciNotation("Radius: ")
        bodies.append(Body(name,color,position,velocity,mass,radius)) #A new body is appended to the list

#Writes the first row of the csv file so that it can be interpreted as a spreadsheet
firstRow = "time,"
for body in bodies:
    firstRow += body.getName() + " x pos,"
    firstRow += body.getName() + " y pos,"
    firstRow += body.getName() + " x vel,"
    firstRow += body.getName() + " y vel,"
firstRow += "\n"
file.write(firstRow)

#The program should be able to display systems of very different sizes, so this adjusts the DISTANCE_SCALE such that every body in the system is within a quarter of the screen width horizontally and a quarter of the screen height vertically of the origin
scaledWell = False
while not scaledWell: #loop that runs until the conditions are met
    scaledWell = True
    for body in bodies:
        if not (body.getPosition()[0]/DISTANCE_SCALE > -SCREEN_WIDTH/4 and body.getPosition()[0]/DISTANCE_SCALE < SCREEN_WIDTH/4 and body.getPosition()[1]/DISTANCE_SCALE > -SCREEN_HEIGHT/4 and body.getPosition()[1]/DISTANCE_SCALE < SCREEN_HEIGHT/4):
            scaledWell = False
    if scaledWell == False:
        DISTANCE_SCALE = DISTANCE_SCALE*10 #increases DISTANCE_SCALE if conditions aren't met
        print("Distance scale adjusted to "+str(DISTANCE_SCALE)+"meters per pixel")
    elif (body.getPosition()[0]/DISTANCE_SCALE > -SCREEN_WIDTH/40 and body.getPosition()[0]/DISTANCE_SCALE < SCREEN_WIDTH/40 and body.getPosition()[1]/DISTANCE_SCALE > -SCREEN_HEIGHT/40 and body.getPosition()[1]/DISTANCE_SCALE < SCREEN_HEIGHT/40):
        DISTANCE_SCALE = DISTANCE_SCALE/10 #If the bodies are all very close together close to the origin, DISTANCE_SCALE is reduced
        print("Distance scale adjusted to "+str(DISTANCE_SCALE)+"meters per pixel")

running = True #Variable for simulation loop
simTime=0 #keeps track of how long the simulation has been running for
timeA = time.time() #timeA and timeB are used to keep track of the frame rate later on

#calculate initial total mechanicalenergy of each body divided by the body's mass
for body in bodies:
    body.setEnergyPerMass(body.findEnergyPerMass(bodies))

#generate stars to make pretty background
stars = []
isStar = []
for x in range(0,SCREEN_WIDTH+1):
    newRow = []
    for y in range(0,SCREEN_HEIGHT+1):
        newRow.append(False)
    isStar.append(newRow)
#isStar is a 2D array that shows that for every pixel on the screen, it doesn't have a star (hence "False")
for x in range(1,SCREEN_WIDTH):
    for y in range(1,SCREEN_HEIGHT):
        #If the die roll is the right number and there are no adjacent pixels which are stars, a pixel is designated as a star
        dieRoll = random.randint(1,300)
        if dieRoll == 300:
            if not (isStar[x-1][y-1] or isStar[x-1][y] or isStar[x-1][y+1] or isStar[x][y-1] or isStar[x][y+1] or isStar[x+1][y-1] or isStar[x+1][y] or isStar[x+1][y+1]):
                isStar[x][y] = True
for x in range(1,SCREEN_WIDTH):
    for y in range(1,SCREEN_HEIGHT):
        if isStar[x][y]:
            stars.append((x,y)) #stars is now an array with the (x,y) coordinates of every star

screen = pygame.display.set_mode([SCREEN_WIDTH,SCREEN_HEIGHT])
lastShownPositions = [] #used in determining whether the screen needs to be updated, which is only when the bodies have moved enough from their last animated position for the difference to be visible

while running: #main simulation loop, which contains the animation code as well

    for event in pygame.event.get(): #makes the program exit the simulation loop if the X in the top-right corner of the window is clicked
        if event.type == pygame.QUIT:
            running = False
    #Adjusts time scale. If the time scale is too fast, the bodies will essentially "skip around" too much and the results won't be realistic (we need a small delta-t)
    #So the program adjust the time scale such that no body's delta-v during the time interval used is more than 1% its prior velocity (if its prior velocity is at least 100 m/s)
    previousTimeScale = TIME_SCALE
    TIME_SCALE = INIT_TIME_SCALE #Uses 10^6 seconds as a baseline delta-t
    for body in bodies:
        oldspeed = numpy.linalg.norm(body.getVelocity())
        if oldspeed>100:
            tooFast=True
            while tooFast:
                accelmag = numpy.linalg.norm(body.calculateAcceleration(bodies))
                if TIME_SCALE*accelmag/oldspeed >= 10**(-2): #Ensure delta v is less than one percent of previous velocity
                    TIME_SCALE = TIME_SCALE/10
                else:
                    tooFast = False
    if TIME_SCALE != previousTimeScale:
        print("Changed time scale to: "+str(TIME_SCALE)+" seconds per frame from "+str(previousTimeScale)) #notifies user of change to time scale

    simTime += TIME_SCALE #updates counter of time that has passed since start of simulation
    for body in bodies:
        #change velocities such that new velocity equals old velocity plus (acceleration times delta-t)
        body.setVelocity(body.getVelocity()+numpy.multiply(body.calculateAcceleration(bodies),TIME_SCALE))
        #changes positions so that new position equals old position plus (velocity times delta-t)
        body.setPosition(body.getPosition()+numpy.multiply(body.getVelocity(),TIME_SCALE))
        #Because only a conservative force (gravity) acts on the bodies, their total mechanical energy must stay the same. If it hasn't, something went a bit wrong, so the program
        #adjusts their speeds to maintain conservation of energy. The formulae are easier to work with if one takes total mechanical energy divided by mass, and the masses are also constant, so this is fine to use
        newEPM = body.findEnergyPerMass(bodies)
        if not newEPM == body.getEnergyPerMass():
            correctSpeed = (2*(body.getEnergyPerMass()-body.findGPEPerMass(bodies)))**0.5 #If the total mechanical energy divided by the mass isn't the same, it calculates what the speed should be to make it the same
            if not math.isnan(correctSpeed): #for some reason there was a NaN error before, so this avoids it
                uncorrectedSpeed = numpy.linalg.norm(body.getVelocity())
                correctionFactor = correctSpeed/uncorrectedSpeed #Figures out by what factor the speed must change to maintain conservation of energy
                body.setVelocity(numpy.multiply(body.getVelocity(),correctionFactor)) #multiplies the velocity by that factor
        body.recordPosition() #this function is explained where it is defined

    saveData(simTime,bodies,file) #Each time the simulation loop runs, this saves the positions and velocities of all the bodies to the csv file created earlier

    #Rounds positions to nearest pixel. Then, if the pixels occupied by the bodies are different from the last time the screen was updated, the screen will be updated to show the movement
    currentPositions = []
    for body in bodies:
            currentPositions += (int(body.getPosition()[0]/DISTANCE_SCALE),int(body.getPosition()[1]/DISTANCE_SCALE))
    
    if currentPositions != lastShownPositions: #If the bodies have moved enough that the screen will look different when updated, then the screen is updated
        #only updating the screen when the difference is actually perceptibly makes the program run faster
        lastShownPositions = []
        for body in bodies:
            lastShownPositions += (int(body.getPosition()[0]/DISTANCE_SCALE),int(body.getPosition()[1]/DISTANCE_SCALE)) #Records the last positions shown on screen to check against new positions in the future to see
            #if the pixels are different
        offScreen = False
        for body in bodies:
            if body.getPosition()[0]/DISTANCE_SCALE < -SCREEN_WIDTH/2 or body.getPosition()[0]/DISTANCE_SCALE > SCREEN_WIDTH/2 or body.getPosition()[1]/DISTANCE_SCALE < -SCREEN_HEIGHT/2 or body.getPosition()[1]/DISTANCE_SCALE > SCREEN_HEIGHT/2:
                offScreen = True #checks if any of the bodies have drifted off-screen
        if offScreen: #if any of them have, DISTANCE_SCALE is adjusted so that they are all on screen again
            DISTANCE_SCALE = DISTANCE_SCALE*10
            for body in bodies:
                body.clearPixelsAlreadyCovered() #The particular pixels covered by the path will change when the DISTANCE_SCALE does, so the pixelsAlreadyCovered list is cleared
        screen.fill((0,0,0)) #black background
        for star in stars: #draws stars0
            pygame.draw.circle(screen,WHITE,star,1)
        for body in bodies: #draws bodies
            body.drawBody(screen)
        for body in bodies: #draws their paths
            body.drawPath(screen)
        for body in bodies: #draws their name tags
            body.drawName(screen)

        #calculate frame rate
        timeB = time.time()
        elapsed_time = timeB-timeA #determines time since last time the screen was updated (or, the first time the screen is updated, since the simulation loop began)
        frameRate = int(1/elapsed_time) #calculates frame rate
        #If the frame rate is above 60 fps, the program waits a moment such that it goes down to 60 fps, to make the animation speed more consistent
        if (elapsed_time<0.0166):
            time.sleep(0.0166-elapsed_time)
            frameRate = 60
        #Display other stats, including frame rate and approximate distance scale and time scale (relative to real time)
        #displays them in the top left corner of the screen
        frameRateText = fpsfont.render(str(frameRate)+" fps",True,WHITE,BLACK)
        frameRateBox = frameRateText.get_rect()
        frameRateBox.center = (35,20)

        distanceScaleText = fpsfont.render("Distance scale: 10^"+str(int(math.log10(DISTANCE_SCALE)))+" meters per pixel",True,WHITE,BLACK)
        distanceScaleBox = distanceScaleText.get_rect()
        distanceScaleBox.center = (30,40)
        
        if frameRate != 0: #The if statement prevents the program from crashing if the frame rate is so low that it is rounded to 0
            timeScaleText = fpsfont.render("10^"+str(int(math.log10(TIME_SCALE*frameRate)))+"x real speed",True,WHITE,BLACK)
            timeScaleBox = timeScaleText.get_rect()
            timeScaleBox.center = (85,60)
        
        #blit text to screen
        #Without blitting, the screen would not be updated
        screen.blit(frameRateText,frameRateBox)
        screen.blit(distanceScaleText,distanceScaleBox)
        if frameRate != 0: screen.blit(timeScaleText,timeScaleBox) #prevents the program from crashing if the frame rate is so low that it is rounded to 0
        timeA = time.time() #to calculate the frame rate the next time the screen is updated
        #update screen
        pygame.display.flip()

#clear up loose ends
print("Finished")
file.close()
pygame.quit()
