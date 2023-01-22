import numpy as np
import pygame as gui

"""
TURTLE OBLITERATOR 9000
Written by Nicholas Quillin
"""

"""3D Objects & Functions"""


class Point():
    def __init__(self, XCoordinate, YCoordinate, ZCoordinate):
        self.X = XCoordinate
        self.Y = YCoordinate
        self.Z = ZCoordinate

    # This handy dohickie will print it in the format used in the program
    def __repr__(self):
        return "Point({}, {}, {})".format(self.X, self.Y, self.Z)

    # You can use these methods to generate a point on the z-plane to be interpreted by preview or turtle
    def orthographicProjection(self):
        return (Point(self.X, self.Y, 0))

    def perspectiveProjection(self, FOCAL_LENGTH):
        # I did it this way because Quaternions make my brain hurt
        perspectiveMagnitude = np.tan(findDivergenceAngle(Point(0, 0, 0 - FOCAL_LENGTH), ORIGIN, self)) * FOCAL_LENGTH
        orthographicMagnitude = findDistance(ORIGIN, self.orthographicProjection())
        return (Point(
            (self.X * perspectiveMagnitude) / orthographicMagnitude,
            (self.Y * perspectiveMagnitude) / orthographicMagnitude,
            0
        ))

    # You can use these methods to transform a point in space
    def scale(self, magnitude):
        return Point(self.X * magnitude, self.Y * magnitude, self.Z * magnitude)

    def rotateAroundZaxis(self, rotation):
        return Point(self.X * np.cos(rotation) - self.Y * np.sin(rotation),
                     self.X * np.sin(rotation) + self.Y * np.cos(rotation),
                     self.Z)

    def rotateAroundXaxis(self, rotation):
        return Point(self.X,
                     self.Y * np.cos(rotation) - self.Z * np.sin(rotation),
                     self.Y * np.sin(rotation) + self.Z * np.cos(rotation))

    def rotateAroundYaxis(self, rotation):
        return Point(self.X * np.cos(rotation) - self.Z * np.sin(rotation),
                     self.Y,
                     self.X * np.sin(rotation) + self.Z * np.cos(rotation))

    # why didnt I do this for rotation? I HAVE NO CLUE
    def transpose(self, magnitude, axis):
        if axis == 'X':
            return Point(self.X + magnitude, self.Y, self.Z)
        elif axis == 'Y':
            return Point(self.X, self.Y + magnitude, self.Z)
        elif axis == 'Z':
            return Point(self.X, self.Y, self.Z + magnitude)
        else:
            print("Invalid transposition on axis {}".format(axis))

    # this makes transforms a point via a transformation preset which is useful when you want to apply multiple transforms at once
    def transform(self, transformation):
        return (self.scale(transformation.SCALE)
                .rotateAroundXaxis(transformation.X_ROTATION)
                .rotateAroundYaxis(transformation.Y_ROTATION)
                .rotateAroundZaxis(transformation.Z_ROTATION)
                .transpose(transformation.X_SHIFT, 'X')
                .transpose(transformation.Y_SHIFT, 'Y')
                .transpose(transformation.Z_SHIFT, 'Z'))


# I will one day learn how to use data object
class TransformationPreset():
    def __init__(self, scale, rotateX, rotateY, rotateZ, shiftX, shiftY, shiftZ, ):
        self.SCALE = scale
        self.X_ROTATION = rotateX
        self.Y_ROTATION = rotateY
        self.Z_ROTATION = rotateZ
        self.X_SHIFT = shiftX
        self.Y_SHIFT = shiftY
        self.Z_SHIFT = shiftZ


ORIGIN = Point(0, 0, 0)


# I could of made a vector object but no, I am stupid
def findDotProduct(tip1, tail1, tip2, tail2):
    return (
        # tip-tail is the vector from tip to tail, I did this to save computation
            ((tip1.X - tail1.X) * (tip2.X - tail2.X))
            + ((tip1.Y - tail1.Y) * (tip2.Y - tail2.Y))
            + ((tip1.Z - tail1.Z) * (tip2.Z - tail2.Z))
    )


# Pythagrias, I love you
def findDistance(point1, point2):
    return (np.sqrt(
        (point2.X - point1.X) ** 2
        + (point2.Y - point1.Y) ** 2
        + (point2.Z - point1.Z) ** 2
    ))


# Returns Divergent angle in RADIANS
def findDivergenceAngle(fulcrum, point1, point2):
    # sometimes the same point can be called consecutively, so I wrote this exception to prevent a NAN error
    if findDistance(fulcrum, point1) * findDistance(fulcrum, point2) == 0:
        print("distance is 0, there is no angle!")
        return (0)
    return (
        np.arccos(
            findDotProduct(point1, fulcrum, point2, fulcrum) / (findDistance(fulcrum, point1) * findDistance(fulcrum, point2))
        ))


"""Visual Preview"""

# ehhhh, presets
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# I put this here so this can work as a library
PREVIEW_WINDOW = (700, 500)

# This refers to a pygame preview window, so you can see what turtle will do before committing to it!
class Renderer():
    def __init__(self, previewWindow, color, focalLength):
        self.color = color
        self.focalLength = focalLength
        self.screen = gui.display.set_mode(previewWindow)

    # Look woody, boiler plate everywhere!
    def runWindow(self, shape):
        gui.display.set_caption('Render Preview')
        self.screen.fill(self.color)
        gui.display.flip()
        self.drawShape(shape)
        gui.display.flip()
        running = True
        while running:
            for event in gui.event.get():
                if event.type == gui.QUIT:
                    running = False

    # this is less reliable than your ex
    def refresh(self):
        gui.display.flip()

    # Here are the function to draw stuff
    def drawLine(self, tail, tip, color):
        gui.draw.line(self.screen, color, coordinateConversion(tail), coordinateConversion(tip))

    def drawLoop(self, loop):
        i = len(loop)
        while i > 0:
            self.drawLine(loop[i - 1].perspectiveProjection(self.focalLength),
                          loop[i - 2].perspectiveProjection(self.focalLength),
                          BLACK)
            i -= 1

    def drawShape(self, shape):
        for loop in shape:
            self.drawLoop(loop)
        gui.display.update()


# Returns a shape
# A shape is a list of loops which themselves is a list of points
# when you project points onto a plane you can keep the order for the lines to generate a final image!
def interpretAsciiSTL(file, transformation):
    with open(file) as rawfile:
        shape = []
        loopqueue = []
        for line in rawfile:
            if not ('vertex' in line):
                if len(loopqueue) != 0:
                    shape.append(loopqueue)
                    loopqueue = []
                continue
            print(line)
            # I am sure that there is a better way of reformating the vectors, but I dont care
            vertexArguments = line.split(' ')
            vertexArguments.pop(0)
            vertexArguments[2] = vertexArguments[2].strip()
            vertex = Point(float(vertexArguments[0]), float(vertexArguments[1]), float(vertexArguments[2]))
            # for static images you need to apply this transform once therefor doing it here saves computation.
            # If you want to animate this, just write your own function to loop through points before rendering!
            vertex = vertex.transform(transformation)
            loopqueue.append(vertex)
    return (shape)


# I know I can use np.degrees, but I have a suspicion that this is faster
def degrees(angle):
    return angle * (180 / np.pi)


# pygame is stupid and has a weird coordiate system, this is the best I can do to convert that to cartesian
def coordinateConversion(point):
    if point.Z != 0:
        pass
    return (PREVIEW_WINDOW[0] / 2 - point.X, PREVIEW_WINDOW[1] / 2 + point.Y)


"""Turtle renderer"""


# You better watch out, you better not cry, cuz turtle is inside . . . your house
class Turtle:
    def __init__(self, xPosition, yPosition, angle, FOCAL_LENGTH, compiler=None):
        self.xPosition = xPosition
        self.yPosition = yPosition
        self.angle = angle
        self.FOCAL_LENGTH = FOCAL_LENGTH
        # support for alterate compilers
        if compiler is None:
            self.compiler = TurtleCompiler()
        else:
            self.compiler = compiler

    # first element is direction angle in radians second is magnitude
    def moveTurtle(self, point):
        self.xPosition = point.X
        self.yPosition = point.Y

    # this will turn turtle parallel to a vector and it was a pain in the asscheeks
    def turn(self, targetVector):
        headingVector = Point(np.cos(self.angle), np.sin(self.angle), 0)
        correctionAngle = findDivergenceAngle(ORIGIN, headingVector, Point(1, 0, 0))
        if headingVector.Y < 0:
            targetVector = targetVector.rotateAroundZaxis(correctionAngle)
        if headingVector.Y > 0:
            targetVector = targetVector.rotateAroundZaxis(-correctionAngle)
        turnAngle = findDivergenceAngle(ORIGIN, targetVector, Point(1, 0, 0))
        if targetVector.Y < 0:
            turnAngle = -turnAngle
        self.compiler.generateTurnCommand(turnAngle)
        self.angle += turnAngle

    # this will move turtle between points, allowing us to use coordinates, which is what stl is made of!
    def move(self, targetPoint, isDrawing):
        centeredVector = Point(targetPoint.X - self.xPosition, targetPoint.Y - self.yPosition, 0)
        self.turn(centeredVector)
        self.compiler.generateMoveCommand(findDistance(ORIGIN, centeredVector), isDrawing)
        self.xPosition = targetPoint.X
        self.yPosition = targetPoint.Y

    # this resets turtle, so if you want to do another object you can do so
    def returnToOrigin(self):
        self.move(Point(0, 0, 0), False)
        self.turn(Point(1, 0, 0))

    # Self-Explainitory
    def drawShape(self, shape):
        endpoint = ORIGIN
        for loop in shape:
            for point in loop:
                loop[loop.index(point)] = point.perspectiveProjection(self.FOCAL_LENGTH)
        for loop in shape:
            self.compiler.comment(" loop #{} : {}".format(shape.index(loop), loop))
            self.move(loop[-1], False)
            for point in loop:
                self.move(point, True)
        self.returnToOrigin()


# This will be generated WITH turtle, so call the turtle object FIRST
# This is configured for Javascript turtle which is what code.org uses
# If you want to make your own compiler, you can change it with polymorphism and inhearitance
# if you do so dont forget to pipe it into the end of the turtle object
class TurtleCompiler():
    def __init__(self):
        self.script = []

    #
    def compileToConsole(self):
        for line in self.script:
            print(line)

    def generateMoveCommand(self, magnitude, IS_DRAWING):
        if magnitude != 0:
            if IS_DRAWING:
                self.script.append("moveForward({});".format(magnitude))
            if not IS_DRAWING:
                self.script.append("jumpForward({});".format(magnitude))

    def generateTurnCommand(self, angle):
        if angle > 0:
            self.script.append("turnRight({});".format(degrees(angle)))
        if angle < 0:
            self.script.append("turnLeft({});".format(degrees(0 - angle)))

    def generateCustomCommands(self, commandName, value):
        self.script.append("{}({});".format(commandName, value))

    def comment(self, comment):
        self.script.append("//{}".format(comment))


"""Execute as Script"""
# This part of the code runs in the case that it is executed like a file

def main():
    FOCAL_LENGTH = 1000
    viewport = Renderer(PREVIEW_WINDOW, WHITE, FOCAL_LENGTH)
    preset = TransformationPreset(10, 0, .5, 0, 0, 0, 100)
    cube = interpretAsciiSTL('3dS.txt', preset)
    turtle = Turtle(0, 0, 0, FOCAL_LENGTH)
    turtle.drawShape(cube)
    turtle.compiler.compileToConsole()
    viewport.runWindow(cube)
    viewport.refresh()


if __name__ == '__main__':
    main()
