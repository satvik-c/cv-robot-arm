import socket
import time

clientSocket = None

def connect(host, port):
    global clientSocket

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port))

def sendState(angBase, angShoulder, angElbow, angWrist, angHand):
    global clientSocket  # Access the global client socket for communication

    # Check if a connection to the robot controller is established
    if clientSocket is None:
        print("No connection established.")
        return

    # Continuously send joint angle states to the robot
    while True:
        try:
            # Create a list of the current joint angles for each part of the robotic arm
            jointStates = [angBase, angShoulder, angElbow, angWrist, angHand]
            
            # Convert the list to a comma-separated string and append a newline
            data = ','.join(map(str, jointStates)) + '\n'
            print(f"Sending data: {data}")

            # Send the joint angle data over the socket to the robot controller
            clientSocket.sendall(data.encode('utf-8'))
            
            # Small delay between transmissions to avoid data loss
            time.sleep(0.003)
        
        # Handle any socket errors
        except (socket.error, OSError) as e:
            print(f"Error sending data: {e}")
            clientSocket.close()
            break


def close():
    global clientSocket
    if clientSocket:
        try:
            clientSocket.close()
            print("Connection closed.")
        except (socket.error, OSError) as e:
            print(f"Error closing the connection: {e}")
        finally:
            clientSocket = None
