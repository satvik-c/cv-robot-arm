import cv2 as cv
import numpy as np

def scan():
    # Open video capture
    capture = cv.VideoCapture(1)

    # Capture a frame from the camera
    isTrue, raw_img = capture.read()

    # Crop the captured image
    img = raw_img[70:240, 20:440]

    # Error checks
    if not isTrue:
        print("Failed to capture image from camera.")
        capture.release()
        cv.destroyAllWindows()
        return None, None, None

    # Convert to grayscale and apply Gaussian blur
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (5, 5), cv.BORDER_DEFAULT)
    
    # Apply adaptive thresholding to binarize the image
    thresh = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2)

    # Find contours in the thresholded image
    contours, _ = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    centerX, centerY = None, None

    # Process the second largest contour (it counts the entire frame as the largest contour)
    if len(contours) > 1:
        contours = sorted(contours, key=cv.contourArea, reverse=True)
        c = contours[1]  # Select second largest contour

        # Get the minimum area rectangle and its bounding box
        rect = cv.minAreaRect(c)
        box = cv.boxPoints(rect)
        box = np.int32(box)

        # Draw the bounding box and center point
        cv.polylines(img, [box], isClosed=True, color=(0, 255, 0), thickness=2)
        centerX, centerY = map(int, rect[0])  # Center coordinates of the rectangle
        cv.circle(img, (centerX, centerY), 5, (0, 0, 255), -1)

        # Get the minimum rectangle width to calculate the gripper width
        widthPix = min(rect[1])

        print(f"Center coordinates: ({centerX}, {centerY})")
        print(f"Width: {widthPix}")

    # Display the processed image
    cv.imshow("img", img)
    cv.waitKey(0)
    capture.release()
    cv.destroyAllWindows()

    return centerX, centerY, widthPix

def process(x, y, width):
	scale = 37
	
	x /= scale
	y /= scale
	width -= 15
	width /= scale
	
	temp = x
	x = y
	y = temp
	
	x += 2.8
	y -= (210/scale)
	width *= 80
	
	z = 0
	w = 0
	
	return x, y, z, w, width

def main():
	h = 2
	clawH = 1.5
	while True:
		input("Press ENTER to initiate a scan...")
		centerX, centerY, widthPix = scan()
		x, y, z, w, width = scan(centerX, centerY, widthPix)
		z = float(input("Enter the height of the object in inches: ")) - clawH
		input(f"Press ENTER to grab at: ({x}, {y}, {z+clawH}, {w})")
		moveInLine(x, y, z+h, w)
		moveHand(30)
		moveInLine(x, y, z, w)
		moveHand(180-width)
		moveInLine(x, y, z+h, w)
		moveInLine(0, -5, 5, w)
		moveHand(30)
