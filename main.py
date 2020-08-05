import pyautogui
from multiprocessing import cpu_count, Queue
import numpy as np
import cv2
from workers import Calculator


def createRasterPreset(steps, step_size, step_rest):
    """Creates a raster for one axis each

    Parameters:
    steps (int): amount of parts the axis shall be split into
    steps_size (int): average pixel size for each step
    step_rest (int): amount of pixels which are added in last iteration

    Returns:
    list: [step_start_coordinate, step_end_coordinate]

    """
    output = []
    counter = 0

    for i in range(steps):
        buffer = [counter]
        counter += step_size
        output.append(buffer + [counter])
    
    output[-1][1] += step_rest

    return output    


def createRaster(w, h, parts):
    """Create raster from image and cpus cores used for processing in taskqueue

    Parameters:
    w (int): total width of image
    h (int): total height of image
    parts (int): parts in which axis is to be split

    Returns:
    list: [[start_width, start_height], [end_width, end_height]]

    """
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
    """Adds tasks for the processes to taskque

    Parameters:
    w (int): total width of image
    h (int): total height of image
    zoom (int): zoomfactor of image
    cpus (int): total amount of cpus used
    queue (multiprocessing.Queue) taskqueue

    Returns:
    int: Total amount of tasks added to taskque
    """  

    raster = createRaster(w, h, cpus)

    for part in raster:
        queue.put([w, h, zoom, part])

    return len(raster)


if __name__ == "__main__": 
    w,h = pyautogui.size() # Size of output fractal in pixel
    zoom = 1 # Zoom factor
    cpus_amount = cpu_count() # Get amount of cores for latter rastering of image
    img = np.ones((h, w, 3), dtype="uint8" )
    taskqueue = Queue(cpus_amount**2+cpus_amount) # Create queue and set maxsize to have room for poison 
    resultqueue = Queue(cpus_amount**2+1)
    tasks_amount = getArgumentsForProcesses(w, h , zoom, cpus_amount, taskqueue)
    cv2.namedWindow("fractal", cv2.WND_PROP_ASPECT_RATIO) # fit window to screen
    cv2.setWindowProperty("fractal", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # set property to fullscreen
    cv2.imshow("fractal", img)
    cv2.waitKey(1)
    processes = []
    
    for i in range(int(cpus_amount/2)): # Fastet configuration
        process = Calculator(taskqueue, resultqueue)
        taskqueue.put(None) # Add poison
        process.start()
        processes.append(process)
          
    # Live rendering of image
    results_retrieved = 0
    rendering_time = 0
    while results_retrieved < tasks_amount:
        result = resultqueue.get()
        results_retrieved += 1

        for x,y,i in result:
            color = bin((i << 21) + (i << 10) + i*8) # shift bits for color effect
            img[y,x] = np.array( [int(color[-8:], 2), int(color[-16:-8], 2), int(color[-24:-16].replace("0b", "").replace("b", ""), 2) ]) # convert bitstring back into colors
        
        cv2.imshow("fractal", img)
        cv2.waitKey(1)

    for p in processes:
        p.join()
        p.close()

    cv2.imshow("fractal",img)
    cv2.waitKey(0) # press any key to shutdown output window
    cv2.destroyAllWindows()

