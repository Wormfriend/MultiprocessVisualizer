import pyautogui
from multiprocessing import cpu_count, Queue
import numpy as np
import cv2
from workers import Calculator
from time import sleep


def createRasterPreset(steps, step_size, step_rest):
    output = []
    counter = 0

    for i in range(steps):
        buffer = [counter]
        counter += step_size
        output.append(buffer + [counter])
    
    else:
        output[-1][1] += step_rest

    return output    


def createRaster(w, h, zoom, parts):
    average_width = w//parts
    average_height = h//parts
    rest_width = w%parts
    rest_height = w%parts
    widths = createRasterPreset(parts, average_width, rest_width)
    heights = createRasterPreset(parts, average_height, rest_height)
    raster = []

    for w in widths:
         for h in heights:
             raster.append([w, h])

    return raster
            

def getArgumentsForProcesses(w, h, zoom, cpus, queue):
    raster = createRaster(w, h, zoom, cpus)

    for part in raster:
        queue.put([w, h, zoom, part])


if __name__ == "__main__": 
    w,h = pyautogui.size() # Size of output fractal in pixel
    zoom = 1 # Zoom factor
    cpus_amount = cpu_count() # Get amount of cores for latter rastering of image
    img = np.ones((h, w, 3), dtype="uint8" )
    taskqueue = Queue(cpus_amount**2+cpus_amount) # Create queue and set maxsize to have room for poison 
    resultqueue = Queue(cpus_amount**2+1)
    getArgumentsForProcesses(w, h , zoom, cpus_amount, taskqueue)
    cv2.namedWindow("fractal", cv2.WND_PROP_ASPECT_RATIO) # fit window to screen
    cv2.setWindowProperty("fractal", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # set property to fullscreen
    cv2.imshow("fractal", img)
    cv2.waitKey(1)

    processes = []
    
    for i in range(cpus_amount):
        process = Calculator(taskqueue, resultqueue)
        taskqueue.put(None) # Add poison
        process.start()
        processes.append(process)

    # Live rendering of image
    while not resultqueue.empty():
        for x,y,i in resultqueue.get():
            color = bin((i << 21) + (i << 10) + i*8)
            img[y,x] = np.array( [int(color[-8:], 2), int(color[-16:-8], 2), int(color[-24:-16].replace("0b", "").replace("b", ""), 2) ])

        cv2.imshow("fractal", img)
        cv2.waitKey(1)

    else:
        for p in processes:
            p.join()
            p.close()

    cv2.imshow("fractal",img)
    cv2.waitKey(0) # press any key to shutdown output window
    cv2.destroyAllWindows()