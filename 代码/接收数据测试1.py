import time, image,sensor,math,pyb,ustruct
from image import SEARCH_EX, SEARCH_DS
from pyb import LED

#从imgae模块引入SEARCH_EX和SEARCH_DS。使用from import仅仅引入SEARCH_EX,
#SEARCH_DS两个需要的部分，而不把image模块全部引入。


sensor.reset()

# Set sensor settings
sensor.set_contrast(1)
sensor.set_gainceiling(16)
# Max resolution for template matching with SEARCH_EX is QQVGA
sensor.set_framesize(sensor.VGA)
# You can set windowing to reduce the search image.
sensor.set_pixformat(sensor.RGB565)



rx_buff=[]
state = 0
tx_flag = 0

x = 0

Find_Task =1       #1
Target_Num =0
data = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]


uart = pyb.UART(3, 115200, timeout_char = 1000)     #定义串口1变量
led =LED(2)




clock = time.clock()
# Run template matching
while (True):

    clock.tick()
    img = sensor.snapshot()# 镜头初始化
    if(uart.any()>0):
       temp = uart.read(3)
       if(temp[0] == 49):
        led.on()
        print(temp[0])

