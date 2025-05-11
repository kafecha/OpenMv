# 二维码例程
#
# 这个例子展示了OpenMV Cam使用镜头校正来检测QR码的功能（请参阅qrcodes_with_lens_corr.py脚本以获得更高的性能）。
import sensor, time
from pyb import UART
import ustruct
from pyb import LED



sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)  # 必须关闭此功能，以防止图像冲洗…
clock = time.clock()
sensor.set_auto_gain(False)  # 关闭自动增益，确保颜色跟踪不受环境光影响，避免图像质量变化
sensor.set_auto_whitebal(False)  # 关闭自动白平衡，确保颜色跟踪不受环境光和白平衡影响

#初始化串口
uart = UART(3,115200,bits=8, parity=None, stop=1, timeout_char = 1000)#初始化串口三、波特率115200 TXD:P4\PB10 RXD:P5\PB11

# 发送函数（每次发送5字节数据）
def send_five_uchar(c1, c2, c3, c4, c5):
    data = ustruct.pack("<BBBBBBBB",
                       0xA5, 0xA6,
                       c1, c2, c3, c4, c5,
                       0x5B
                       )
    uart.write(data)
    print("Sent:", data)

#运行监测
led =LED(3) # led = pyb.LED(1)表示led表示红灯。各种状态如下:Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.
       #点亮红灯 板载红灯点亮表示程序得到执行

# 数据处理函数
def split_data(data_list, chunk_size=5):
    batches = []
    for i in range(0, len(data_list), chunk_size):
        batch = data_list[i:i+chunk_size]
        batch += [0] * (chunk_size - len(batch))  # 补零填充
        batches.append(batch)
    return batches

saoma_num = 0
saoma_go = 1
neirong = None

while(True):
    clock.tick()
    img = sensor.snapshot()
    img.lens_corr(2.0) # 1.8的强度参数对于2.8mm镜头来说是不错的。

        #以下为扫码
    if(saoma_go == 1):
        for code in img.find_qrcodes():
                img.draw_rectangle(code.rect(), color = (255, 0, 0))
                neirong = code[4]

                if(neirong):
                    saoma_go = 0

                chuli = neirong.encode("UTF-8")

                if saoma_num == 0:
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
                    saoma_num = 1

                elif saoma_num == 1:
                    #C区二维码
                    #分割字节并过滤空项
                    items = [item for item in chuli.split(b'\n') if item]

                    #建立映射字典（保持字节形式匹配）
                    mapping = {
                           b'\xe8\x8c\x84\xe5\xad\x90': '1',  # 茄子 -> 1
                           b'\xe5\x8d\x97\xe7\x93\x9c': '2',  # 南瓜 -> 2
                           b'\xe8\xa5\xbf\xe7\xba\xa2\xe6\x9f\xbf': '3',  # 西红柿 -> 3
                           b'\xe8\xbe\xa3\xe6\xa4\x92': '4'   # 辣椒 -> 4
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

                    # 分两次发送（每组数据分两次，共四次发送）
                    group1_batches = split_data(group1)
                    group2_batches = split_data(group2)

                    # 发送group1的两批数据
                    print("发送 Group1 数据：")
                    for batch in group1_batches:
                        send_five_uchar(*batch)

                    # 发送group2的两批数据
                    print("\n发送 Group2 数据：")
                    for batch in group2_batches:
                        send_five_uchar(*batch)



