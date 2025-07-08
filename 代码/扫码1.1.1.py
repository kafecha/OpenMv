
import sensor,  time,  display
from pyb import UART
import ustruct
from pyb import LED

# 苹果 -> 1
# 梨子 -> 2

# 茄子 -> 3
# 南瓜 -> 4
# 西红柿 -> 5
# 辣椒 -> 6

led =LED(2)

color_A_thresholds = [
((15, 41, 30, 50, 0, 37),'qj',(255, 165, 0)),# 成熟青椒
((10, 56, 0, 55, -15, 27),'xhs',(255, 165, 0)),#成熟西红柿
((5, 25, -11, 8, -23, 15),'yc',(128,0,128)),#成熟洋葱
((29, 77, 5, 41, 24, 49),'ng',(255,165,0)),#成熟南瓜
((8, 100, -44, -17, -18, 40),'wcs',(0, 255, 255)),#未成熟
]


# 定义多种颜色的阈值
color_thresholds = [
    ((0, 100, 20, 127, 127, -10), 'red', (255, 165, 0)),  # 红色阈值
    ((30, 100, -64, -8, -32, 32), 'green', (0, 255, 255)),  # 绿色阈值
    ((50, 100, -28, 0, 32, 51), 'li-ripe', (0, 255, 255)),  # 成熟
    ((35, 55, -41, -30, 29, 45),'apple-immaturate',(0,255,0)),
    ((23, 40, -31, -13, 35, 45),'pear-immaturate',(255,255,255)),
    ((15, 41, 30, 50, 0, 37),'qj',(255,255,255)),# 成熟青椒
    ((10, 56, 0, 55, -15, 27),'xhs',(255,255,255)),#成熟西红柿
    ((5, 25, -11, 8, -23, 15),'yc',(255,255,255)),#成熟洋葱
    ((29, 77, 5, 41, 24, 49),'ng',(255,255,255)),#成熟南瓜
    ((8, 100, -44, -17, -18, 40),'wcs',(0, 255, 255)),#未成熟
]

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)  # 必须关闭此功能，以防止图像冲洗…
clock = time.clock()
sensor.set_auto_gain(False)  # 关闭自动增益，确保颜色跟踪不受环境光影响，避免图像质量变化
sensor.set_auto_whitebal(False)  # 关闭自动白平衡，确保颜色跟踪不受环境光和白平衡影响

lcd = display.SPIDisplay()
clock = time.clock()
area_threshold = 500  # 设置面积阈值
K = 1150  # 初始K值
last_print_time = time.time()  # 记录上一次打印的时间
uart = UART(3, 115200, timeout_char=1000)  # 初始化串口通信
length = 0  # 给length一个默认值，以防没有任何色块被检测到


#初始化串口
uart = UART(3,115200,bits=8, parity=None, stop=1, timeout_char = 1000)#初始化串口三、波特率115200 TXD:P4\PB10 RXD:P5\PB11

# 发送函数（每次发送8字节数据）
def send_eight_uchar(c1, c2, c3, c4, c5, c6, c7, c8):
    data = ustruct.pack("<BBBBBBBB",
                       c1, c2, c3, c4, c5, c6, c7, c8,
                       )
    uart.write(data)
    print("Sent:", data)

#运行监测
led =LED(3) # led = pyb.LED(1)表示led表示红灯。各种状态如下:Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.
       #点亮红灯 板载红灯点亮表示程序得到执行

# 数据处理函数
def split_data(data_list, chunk_size=8):
    batches = []
    for i in range(0, len(data_list), chunk_size):
        batch = data_list[i:i+chunk_size]
        batch += [0] * (chunk_size - len(batch))  # 补零填充
        batches.append(batch)
    return batches

saoma_num = 0  #扫码次数
saoma_go = 1   #0-识别颜色  1-扫码  3-什么都不干  可以发送对应数字改变运行状态
neirong = None #扫码内容存放变量

while(True):
    led.on()
    clock.tick()
    img = sensor.snapshot()
    img.lens_corr(2.0) # 扫码用的 用来使照片平整 1.8的强度参数对于2.8mm镜头来说是不错的。

    selected_blob = None
    selected_blob_pixels = 0
    min_length = float('inf')
    color_code = 0  # 每次循环迭代开始时重新初始化颜色代码为0（未检测到）
    display_text = "未检测到色块"  # 初始化显示文本
    uart_data_display = ""  # 初始化串口数据显示文本

    #以下为接收区
    if(uart.any()>0):
       temp = uart.read(3)
       print(temp[0])
       if(temp[0] == 49):
        saoma_go = 1
       if(temp[0] == 48):
        saoma_go = 0
    #以上为接收区


    if(saoma_go == 0):
        # 多颜色识别
        for threshold, color_name, frame_color in color_A_thresholds:
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



    #以下为扫码
    if(saoma_go == 1):
        for code in img.find_qrcodes():
            img.draw_rectangle(code.rect(), color = (255, 0, 0))
            neirong = code[4]
            chuli = neirong.encode("UTF-8")
            if saoma_num == 1:
                #B区二维码
                # 按换行符分割字节串（去除空项）
                items = [item for item in chuli.split(b'\n') if item]

                # 映射字典定义
                mapping = {
                   b'\xe8\x8b\xb9\xe6\x9e\x9c': '1',  # 苹果 -> 1
                   b'\xe6\xa2\xa8\xe5\xad\x90': '2'   # 梨子 -> 2
                   }

                # 处理每个字节片段并重组
                result = '\n'.join([mapping.get(item, '') for item in items])

                # 输出结果
                print(result)
                # 转换为整数列表
                data_list = [int(line.strip()) for line in result.split() if line.strip()]
                # 分批次后的数据
                batches = split_data(data_list)
                for batch in batches:
                    send_eight_uchar(*batch)
                saoma_go = 3
                saoma_num = 1

            elif saoma_num == 0:
                #C区二维码
                #分割字节并过滤空项
                items = [item for item in chuli.split(b'\n') if item]

                #建立映射字典（保持字节形式匹配）
                mapping = {
                       b'\xe8\x8c\x84\xe5\xad\x90': '3',  # 茄子 -> 3
                       b'\xe5\x8d\x97\xe7\x93\x9c': '4',  # 南瓜 -> 4
                       b'\xe8\xa5\xbf\xe7\xba\xa2\xe6\x9f\xbf': '5',  # 西红柿 -> 5
                       b'\xe8\xbe\xa3\xe6\xa4\x92': '6'   # 辣椒 -> 6
                   }

                #分离数字部分（识别末尾的纯数字字符串）
                group1_items = []
                group2_str = ""
                for item in items:
                       if b',' in item and all(c in b'0123456789,' for c in item):
                           group2_str = item.decode('utf-8').replace(',', ' ')
                       else:
                           group1_items.append(mapping.get(item, ''))

                group1 = [int(x) for x in group1_items]
                group2 = list(map(int, group2_str.split()))

                # 分两次发送（每组数据发一次，共两次次发送）
                group1_batches = split_data(group1)
                group2_batches = split_data(group2)

                # 发送水果名字
                print("发送 Group1 数据：")
                for batch in group1_batches:
                    send_eight_uchar(*batch)

                # 发送采摘顺序
                print("\n发送 Group2 数据：")
                for batch in group2_batches:
                    send_eight_uchar(*batch)
                saoma_go = 0
