from multiprocessing import Process, Pool
import numpy as np
import cv2


class Calculator(Process):
    def __init__(self, taskqueue, resultqueue):
        Process.__init__(self)
        self.taskqueue = taskqueue
        self.resultqueue = resultqueue


    def drawPartialFractal(self, *args):
        width, height, zoom = args[0][:3]
        width_start, width_end = args[0][3][0]
        height_start, height_end = args[0][3][1]
        cX, cY = -0.7, 0.27015
        maxIter = 255
        output = []

        for x in range(width_start, width_end): 
            for y in range(height_start, height_end): 
                zx = 1.5*(x - width/2)/(0.5*zoom*width) 
                zy = 1.0*(y - height/2)/(0.5*zoom*height) 
                i = maxIter 

                while zx*zx + zy*zy < 4 and i > 1: 
                    tmp = zx*zx - zy*zy + cX 
                    zy,zx = 2.0*zx*zy + cY, tmp 
                    i -= 1
    
                output.append((x,y,i))

        return output


    def run(self):
        while True:
            args = self.taskqueue.get()

            if args == None:
                break
            
            self.resultqueue.put(self.drawPartialFractal(args))
            



