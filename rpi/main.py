from object_detection import scan, process
from movement import moveInLine
from send_data import connect, sendState, close

def main():
    host = '192.168.1.21'
    port = 12345
    #connect(host, port)

    try:
        while True:
            x, y, width = scan()

            if x is not None and y is not None and width is not None:
                x, y, z, w, width = process(x, y, width)

                angBase, angShoulder, angElbow, angWrist, angHand = moveInLine(x, y, z, w)

                #sendState(angBase, angShoulder, angElbow, angWrist, angHand)

    except KeyboardInterrupt:
        print("Program interrupted. Closing connection...")
    #finally:
        close()

if __name__ == "__main__":
    main()

                


