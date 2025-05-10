import sensor, image, time, math, display
from pyb import UART
from pyb import LED

led =LED(2)

# 定义多种颜色的阈值
color_thresholds = [
    ((0, 100, 20, 127, 127, -10), 'red', (255, 165, 0)),  # 红色阈值
    ((30, 100, -64, -8, -32, 32), 'green', (0, 255, 255)),  # 绿色阈值
]

# 初始化摄像头和LCD
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)  # 适配LCD屏幕大小128x160
lcd = display.SPIDisplay()
clock = time.clock()
area_threshold = 500  # 设置面积阈值
K = 1150  # 初始K值
last_print_time = time.time()  # 记录上一次打印的时间
uart = UART(3, 115200, timeout_char=1000)  # 初始化串口通信
length = 0  # 给length一个默认值，以防没有任何色块被检测到
while True:

    led.on()
    clock.tick()
    img = sensor.snapshot()  # 拍照
    selected_blob = None
    selected_blob_pixels = 0
    min_length = float('inf')
    color_code = 0  # 每次循环迭代开始时重新初始化颜色代码为0（未检测到）
    display_text = "未检测到色块"  # 初始化显示文本
    uart_data_display = ""  # 初始化串口数据显示文本

    # 多颜色识别
    for threshold, color_name, frame_color in color_thresholds:
        blobs = img.find_blobs([threshold], pixels_threshold=100, area_threshold=area_threshold, merge=True)
        for blob in blobs:
            if blob.pixels() >= area_threshold:
                b = blob.rect()
                img.draw_rectangle(b, color=frame_color)
                img.draw_cross(blob.cx(), blob.cy())
                Lm = (b[2] + b[3]) / 2
                length = K / Lm
                if (color_name == 'red' and (length < min_length or not selected_blob)) or (color_name == 'green' and not selected_blob and length < min_length):
                    selected_blob = (blob, frame_color, color_name, length)
                    selected_blob_pixels = blob.pixels()
                    min_length = length
                    color_code = 1 if color_name == 'red' else 2
                    display_text = f"Color: {color_name}\nDistance: {length:.2f} \nX={blob.cx()}, Y={blob.cy()}\nArea: {selected_blob_pixels}"

    # 检查是否有选中的色块
    if selected_blob:
        blob, frame_color, color_name, length = selected_blob
        b = blob.rect()
        img.draw_rectangle(b, color=(255, 0, 0), thickness=2)  # 使用红色框突出显示
        img.draw_cross(blob.cx(), blob.cy())

        # 构建并发送数据
        x4 = blob.cx() // 256
        num_x = blob.cx() % 256
        num_y = blob.cy()
        img_data = bytearray([0x2C, 18, num_x, x4, num_y, color_code, 0x5B])  # 构建数据包
        uart.write(img_data)  # 通过串口发送数据
        uart_data_display = "UART: " + " ".join(["{:02x}".format(x) for x in img_data])
    else:
        # 如果没有检测到色块，发送默认数据
        img_data = bytearray([0x2C, 18, 0, 0, 0, 0, 0x5B])
        uart.write(img_data)
        uart_data_display = "UART: " + " ".join(["{:02x}".format(x) for x in img_data])

    # 显示结果
    if time.time() - last_print_time > 0.4:
        print(display_text)
        last_print_time = time.time()

    img.draw_string(2, 2, display_text, color=(0,0,255), scale=1, mono_space=False)  # 在图像左上角显示识别结果文本
    img.draw_string(2, 150, uart_data_display, color=(255,255,255), scale=1, mono_space=False)  # 显示串口数据
    lcd.write(img)  # 显示图像和文本
