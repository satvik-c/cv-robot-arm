#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Servo driver constants
#define FREQUENCY 50
#define MIN_PULSE_WIDTH 500
#define MAX_PULSE_WIDTH 2600

// Initialize the I2C PWM driver
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Define PCA9685 driver channels for each joint
int base = 15;
int shoulder = 14;
int elbow = 13;
int wrist = 12;
int hand = 10;

// Define analog input pins for potentiometers
int potX = A2;
int potY = A1;
int potZ = A0;
int potWrist = A3;
// Define digital input pin for the gripper button
int handButton = 13;

// Define physical arm constraints
double armLength = 3.54; // length of each arm in INCHES

void setup() {
  Serial.begin(9600);
  
  // Initialize the PWM driver for servo control
  pwm.begin();
  pwm.setPWMFreq(FREQUENCY);
  
  // Configure the hand gripper button with an internal pull-up resistor
  pinMode(handButton, INPUT_PULLUP);
  
  // Set initial gripper state to closed
  moveHand("grab");
  delay(500);
}

// Custom map function to handle floating-point values for precise joint interpolation
double mapFloat(double x, double in_min, double in_max, double out_min, double out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

void loop() {
  // Continuously read inputs and update arm position
  manualControl();
  //autoControl();
}

// Pre-programmed sequence for automated testing
void autoControl() {
  moveToPos(2.86, 0, 0, -90);
  delay(1000);
  moveToPos(6.23, 0, 0, -90);
  delay(1000);
}

// Reads analog potentiometers and converts them to physical spatial coordinates
void manualControl() {
  // Read raw 10-bit analog values (0 to 1023) from potentiometers
  double potXVal = analogRead(potX);
  double potYVal = analogRead(potY);
  double potZVal = analogRead(potZ);
  double potWristVal = analogRead(potWrist);

  // Map raw analog values to physical constraints (in inches/degrees)
  double posX = mapFloat(potXVal, 0, 1023, 0, 7);
  double posY = mapFloat(potYVal, 0, 1023, 7, -7);
  double posZ = mapFloat(potZVal, 0, 1023, 7, -1.55);
  double posWrist = mapFloat(potWristVal, 0, 1023, 90, -90);

  // Execute inverse kinematics to move the arm to the target coordinates
  moveToPos(posX, posY, posZ, posWrist);

  // Log current target coordinates for debugging
  Serial.print(posX); Serial.print(" ");
  Serial.print(posY); Serial.print(" ");
  Serial.print(posZ); Serial.print(" -------- ");

  // Read button state to control gripper (LOW means pressed)
  int handButtonState = digitalRead(13);
  if (handButtonState == LOW) {
    moveHand("release");
    Serial.print("Release"); Serial.print(" -------- ");
  }
  else {
    moveHand("grab");
    Serial.print("Grab"); Serial.print(" -------- ");
  }
}

// Controls the end-effector gripper using predefined servo angles
void moveHand(String action) {
  if(action == "release") {
    // Open gripper (Servo mapped to angle ~91)
    pwm.setPWM(hand, 0, 91);
  }
  else if (action == "grab") {
    // Close gripper (Servo mapped to angle ~179)
    pwm.setPWM(hand, 0, 179);
  }
  else {
    Serial.println("Enter a valid action (grab/release).");
  }
}

// Calculates inverse kinematics to convert spatial (x,y,z) targets into joint angles
void moveToPos(double x, double y, double z, double w) {
  // Verify target is within the physical reach of the arm
  double distance = sqrt(x * x + y * y + z * z);
  if (distance > 2 * armLength) {
    Serial.println("Target position is out of reach!");
    return; // Stop the movement
  }

  // Calculate the base rotation angle in the XY plane
  double b = atan2(y, x) * (180 / PI); 
  
  // Calculate horizontal distance (l) and hypotenuse (h) to the target
  double l = sqrt(x * x + y * y); 
  double h = sqrt(z * z + l * l);
  
  // Calculate internal angles phi and theta for the elbow/shoulder joints
  double phi = atan2(z,l) * (180 / PI);
  double theta = acos((h / 2) / armLength) * (180 / PI);

  // Compute final shoulder (a1) and elbow (a2) joint angles
  double a1 = phi + theta;
  double a2 = (phi - theta);

  // Command servos to the computed angles
  moveToAngle(b, a1, a2, w);

  // Log computed joint angles for debugging
  Serial.print(b); Serial.print(" ");
  Serial.print(a1); Serial.print(" ");
  Serial.print(a2); Serial.print(" ---------- ");
}

// Compensates for physical servo mounting offsets and drives the motors
void moveToAngle(double posBase, double posShoulder, double posElbow, double posWrist) {
  // Base and shoulder move normally based on IK calculation
  pwm.setPWM(base, 0, angleToPWM(posBase, true, false, false, false));
  pwm.setPWM(shoulder, 0, angleToPWM(posShoulder, false, true, false, false));
  
  // Elbow angle is offset by the shoulder's position to keep it relative to the ground
  pwm.setPWM(elbow, 0, angleToPWM(90-posShoulder+posElbow, false, false, true, false));
  
  // Wrist angle is offset by the elbow's position, with an additional 20.5 degree mechanical offset
  pwm.setPWM(wrist, 0, angleToPWM(-posElbow+posWrist+20.5, false, false, false, true));
  Serial.println(-posElbow+posWrist+20.5);
}

// Converts calculated joint angles into specific PWM pulse widths based on servo constraints
int angleToPWM(double angle, bool isBase, bool isShoulder, bool isElbow, bool isWrist) {
  // Convert standard pulse widths to PCA9685 12-bit register values (0-4095)
  // Formula: (Pulse Width / 1,000,000) * Frequency * 4096
  
  if (isBase) {
    // Base servo operates from -90 to 90 degrees
    return double(float(map(angle, -90, 90, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH)) / 1000000 * FREQUENCY * 4096);
  }
  else if (isShoulder) {
    // Shoulder servo is physically inverted (180 to 0)
    return double(float(map(angle, 180, 0, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH)) / 1000000 * FREQUENCY * 4096);
  }
  else if (isElbow) {
    // Elbow servo operates from 90 to -90 degrees
    return double(float(map(angle, 90, -90, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH)) / 1000000 * FREQUENCY * 4096);
  }
  else if (isWrist) {
    // Wrist servo requires a wider pulse range (+/- 200) to reach limits
    return double(float(map(angle, -90, 90, MIN_PULSE_WIDTH-200, MAX_PULSE_WIDTH+200)) / 1000000 * FREQUENCY * 4096);
  }
  
  // Default mapping for unhandled joints (0 to 180 degrees)
  return int(float(map(angle, 0, 180, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH)) / 1000000 * FREQUENCY * 4096);
}