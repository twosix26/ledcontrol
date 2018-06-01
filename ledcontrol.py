import socket
import struct
import json
from flask import Flask, request, make_response

app = Flask(__name__)

# address = ('192.168.20.220', 8800)
port = 8800
address_dic = {1:"192.168.20.220",
               2:"192.168.20.220"
               }

def SendCollectionData2LED(msg):

    data = bytes(msg.encode('gb2312'))                  #发送的数据

    head = bytes([0xfe, 0x5c, 0x4b, 0x89])              #包头，固定不变
    tail = bytes([0xff, 0xff])                          #包尾
    base_set = bytes([0x29, 0x00, 0x11, 0x11])          #基本设置，41号素材，不闪烁，红色字体，（宋体，16*16字号）
    protocol = bytes([0x65, 0x00, 0x00, 0x00, 0x00])    #协议0x65,及转发地址全0
    length_data = struct.pack('<b', len(data))          #数据包长度
    length_ctl = struct.pack('<L', len(data) + 5)       #控制字段长度
    length = struct.pack('<L', len(data) + 24)          #数据包总长
    """数据拼接"""
    sendmessage = head + length + protocol + length_ctl \
                + base_set + length_data + data + tail
    return sendmessage

def BaseSet(len):
    if len <= 16:
        fun = bytes([0x09])                             #立即显示
        speed = bytes([0x01])                           #速度最快
        time = bytes([0xff])                            #一直停留
    else:
        fun = bytes([0x01])                             #右移动
        speed = bytes([0x07])                           #速度最慢
        time = bytes([0x00])                            #不停留
    return fun + speed + time

def AttributeSet(len):
    color = bytes([0x01])
    keep = bytes([0x00])
    if len <= 16:
        font = bytes([0x11])                            #宋体，16*16
    else:
        font = bytes([0x13])                            #宋体，32*32
    return color + font + keep

def SendInternalText(msg):
    data = bytes(msg.encode('gb2312'))                  #发送的数据

    head = bytes([0xfe, 0x5c, 0x4b, 0x89])              #包头，固定不变
    tail = bytes([0xff, 0x00, 0x01, 0x00,
                  0x01, 0x00, 0x01, 0x00,
                  0x00, 0x00, 0xff, 0xff])              #包尾
    protocol = bytes([0x31, 0x00, 0x00, 0x00, 0x00])    #协议0x31,消息ID
    material_uid = bytes([0x30, 0x30, 0x30, 0x30, 0x30,
                          0x30, 0x30, 0x30, 0x31])      #素材UID
    base_set = bytes([0x2c]) + BaseSet(len(data))       #基本设置，分隔符，移动方式，速度，时间
    time = bytes([0x30, 0x31, 0x30, 0x31,
                  0x30, 0x31, 0x39, 0x39,
                  0x31, 0x32, 0x33, 0x31])              #播放时间01年01月01日-99年12月31日
    attributes = bytes([0x13, 0x00, 0x00, 0x00,         #属性长度
                        0x55, 0xAA, 0x00, 0x00,         #标志字节，保留字节
                        0x37, 0x32, 0x32, 0x31,         #内容属性，掉电不保存，立即更新，文本起始
                        0x33, 0x31, 0x00, 0x00,         #三基色，编码方式，保留字节
                        0x08, 0x00, 0x20, 0x00]) + AttributeSet(len(data))       #宽8*8，高32

    length_data = struct.pack('<L', len(data) + 10)     #数据包长度
    length_ctl = struct.pack('<L', len(data) + 62)      #控制字段长度
    length = struct.pack('<L', len(data) + 81)          #数据包总长
    """数据拼接"""
    sendmessage = head + length + protocol + length_ctl \
                + material_uid + base_set + time + attributes \
                + length_data + data + tail
    return sendmessage

def SendCollectionData2VOICE(msg):

    data = bytes(msg.encode('gb2312'))                  #发送的数据

    head = bytes([0xfe, 0x5c, 0x4b, 0x89])              #包头，固定不变
    tail = bytes([0x00, 0x00, 0xff, 0xff])              #包尾
    voice_head = bytes([0xfd])                          #语音包头
    base_set = bytes([0x01, 0x00])                      #播放合成语音，gb2312
    protocol = bytes([0x68, 0x01, 0x00, 0x00, 0x00])    #协议0x68,转发方式rs232-0x01，转发ID全0
    length_data = struct.pack('>H', len(data) + 2)      #数据包长度
    length_ctl = struct.pack('<L', len(data) + 7)       #控制字段长度
    length = struct.pack('<L', len(data) + 26)          #数据包总长
    """数据拼接"""
    sendvoice = head + length + protocol + length_ctl \
              + voice_head + length_data + base_set \
              + data + tail
    return sendvoice

def json_response(data: dict, code: int = 200):
    json_data = json.dumps(data, ensure_ascii=False)
    response = make_response(json_data, code)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/control', methods=['POST', ])
def ControlLED():
    params = request.get_json()
    content: str = params.get("content", "")
    # if not content:
        # return json_response({"msg": "content is required"}, code=400)
    led_id: int = params.get("led_ids", "")
    audio_id: int = params.get("audio_ids", "")
    # TODO: do something
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    senddata = SendInternalText(content)
    for id in led_id:
        if id in address_dic.keys():
            s.sendto(senddata, (address_dic[id], port))

    sendvoice = SendCollectionData2VOICE(content)
    for id in audio_id:
        if id in address_dic.keys():
            s.sendto(sendvoice, (address_dic[id], port))

    s.close()
    return json_response({"msg": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, debug=True)


