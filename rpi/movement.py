import time
import math

# Arm setup
linkLength = 3.5468
grabPos = 180

# Current positions
currentX = 2.0
currentY = 0.0
currentZ = 6.0
currentW = 0.0

angBase = 90
angShoulder = 90
angElbow = 0
angWrist = 90
angHand = 30


def convertAngle(posBase, posShoulder, posElbow, posWrist):
    global angBase, angShoulder, angElbow, angWrist
    angBase = posBase + 90
    angShoulder = 180 - posShoulder
    angElbow = 0 - posElbow + posShoulder
    angWrist = posWrist + 90 - posElbow

    return angBase, angShoulder, angElbow, angWrist, angHand

def moveToPos(x, y, z, w):
    """
    Moves the robotic arm to the specified position (x, y, z, w) by calculating the required 
    joint angles with simplified inverse kinematics.

    Arguments:
        x, y, z: Target coordinates in space.
        w: Angle of the end-effector / wrist.
    """

    # Global variables to keep track of the current position of the arm
    global currentX, currentY, currentZ, currentW

    # Check if the target position is within the reach of the robotic arm
    # The distance is calculated as the Euclidean distance from the origin (0, 0, 0) to (x, y, z)
    distance = math.sqrt(x * x + y * y + z * z)
    
    # If the distance exceeds twice the link's length (2 links in arm excluding wrist), the target position is unreachable
    if distance > (2 * linkLength):
        print("Target pose out of reach!")
        time.sleep(0.1)
        return
    
    # ---------------------------Calculation of required joint angles--------------------------------------

    # Calculate the base angle (b) from the origin to the target (x, y) in the horizontal plane
    b = math.atan2(y, x) * 180 / math.pi

    # Calculate the horizontal distance (l) to the target (x, y)
    l = math.sqrt(x * x + y * y)

    # Calculate the hypotenuse (h) in the vertical plane from the origin to the target (x, y, z)
    h = math.sqrt(z * z + l * l)

    # Calculate the angle (phi) between the horizontal and the line to the target (z, l)
    phi = math.atan2(z, l) * 180 / math.pi

    # Calculate the joint angle (theta) for the arm, using inverse kinematics
    theta = math.acos((h / 2) / linkLength) * 180 / math.pi

    # Compute the two arm joint angles (a1, a2) based on the calculated phi and theta
    # These angles represent the required configuration of the two joints to reach the target
    a1 = phi + theta  # First joint angle
    a2 = phi - theta  # Second joint angle

    # Convert the computed angles into a format that is readable and usable by the servo motors
    convertAngle(b, a1, a2, w)  # Function to send the angles to the servos for actuation

    # Update the current position of the robotic arm to the new target position
    currentX = x
    currentY = y
    currentZ = z
    currentW = w  # Update wrist orientation

def cubicEaser(t):
    """
    Cubic easing function for smooth acceleration (ease-in) and deceleration (ease-out).
    
    Mathematically modeled as:
    - f(t) = 4 * t^3                    for 0 <= t < 0.5  (ease-in)
    - f(t) = 0.5 * (2t - 2)^3 + 1       for 0.5 <= t <= 1  (ease-out)

    Arguments:
        t (float): Progress between 0 and 1.

    Returns:
        float: Eased value of t.
    """
    # Ease-in for the first half (0 <= t < 0.5)
    if t < 0.5:
        return 4 * t * t * t
    
    # Ease-out for the second half (0.5 <= t <= 1)
    else:
        f = (2 * t) - 2
        return 0.5 * f * f * f + 1

def moveInLine(x1, y1, z1, w1):
    """
    Moves in a straight line from the current position (currentX, currentY, currentZ, currentW)
    to the target position (x1, y1, z1, w1) with cubic easing applied.

    Arguments:
        x1, y1, z1, w1: Target coordinates for the new position.
    """

    # Global variables that store the current position
    global currentX, currentY, currentZ, currentW

    # Starting position (current position)
    x0 = currentX
    y0 = currentY
    z0 = currentZ
    w0 = currentW

    # Define how many steps the movement should be divided into
    # More steps result in a smoother and straighter movement
    steps = 30

    # Loop through each step to interpolate between the start and end position
    for i in range(steps):
        # Calculate the interpolation factor 't' for the current step (normalized between 0 and 1)
        t = i / steps

        # Apply a cubic easing function to smooth the transition
        easedT = cubicEaser(t)

        # Interpolate the x, y, z, and w positions using the easing factor
        # Linear interpolation between the starting and target position for each axis
        xt = x0 * (1 - easedT) + x1 * easedT
        yt = y0 * (1 - easedT) + y1 * easedT
        zt = z0 * (1 - easedT) + z1 * easedT
        wt = w0 * (1 - easedT) + w1 * easedT

        # Move to the new interpolated position (xt, yt, zt, wt)
        moveToPos(xt, yt, zt, wt)

        time.sleep(0.04) #40 ms pause to control speed between steps

def moveHand(position):
    global angHand
    if 30 <= position <= 180:
        angHand = position

def autoControl():
    moveInLine(4,0,-0.4,0)
    moveHand(160)
    time.sleep(1)
    moveInLine(4,0,4,0)
    moveHand(30)
    time.sleep(1)
