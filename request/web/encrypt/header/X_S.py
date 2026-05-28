import hashlib
import json
import random
import time
import urllib.parse
from request.web.encrypt.config import xhs_config
from request.web.encrypt.xhs_diy_encode import encode_utf8, b64_encode


class XHS_XS_Encrypt:
    """
    小红书XS加密实现类
    
    用于生成小红书API请求所需的X-S加密头。
    加密过程包括：MD5哈希、Base64编码和AES加密等多个步骤。  
    """

    def __init__(self):
        """初始化加密器，从配置文件读取必要的加密参数
        """
        # 加载其他加密参数
        self.__appID = xhs_config.get('XHS_VERSION', 'APP_ID')
        self.__os_system = xhs_config.get('XHS_VERSION', 'OS_SYSTEM')
        self.__language_version = xhs_config.get('XHS_VERSION', 'LANGUAGE_VERSION')
        self.__base64_table = xhs_config.get('XHS_VERSION', 'BASE64_TABLE')
        self.__xorkey = xhs_config.get('XS_ENCRYPT', 'XOR_KEY')
        self.__x3_prefix = xhs_config.get('XS_ENCRYPT', 'X3_PREFIX')
        self.__x3_base64_table = xhs_config.get('XS_ENCRYPT', 'X3_BASE64_TABLE')

    def __u32_add(self, a, b) -> int:
        return (a + b) & 0xFFFFFFFF

    def __js_left_rotate(self, n, d):
        """JavaScript风格的左移"""
        return ((n << d) | (n >> (32 - d))) & 0xFFFFFFFF
    

    def __diy_hasher(self, data: list) -> bytes:
        """
        自定义哈希函数
        """
        data_length = len(data)

        # 初始化s1, s2, s3, s4
        s1, s2, s3, s4 = (
            1831565813 ^ data_length,
            461845907 ^ (data_length << 8),
            2246822507 ^ (data_length << 16),
            3266489909 ^ (data_length << 24),
        )

        for i in range(0, len(data), 8):            
            v0 = int.from_bytes(bytes(data[i:i+4]), byteorder="little")
            v1 = int.from_bytes(bytes(data[i+4:i+8]), byteorder="little")

            s1 = self.__js_left_rotate(self.__u32_add(s1, v0) ^ s3, 7)
            s2 = self.__js_left_rotate(self.__u32_add(s2 ^ v0, s4), 11)
            s3 = self.__js_left_rotate(self.__u32_add(s3, v1) ^ s1, 13)
            s4 = self.__js_left_rotate(self.__u32_add(s4 ^ v1, s2), 17)

        t1 = s1 ^ data_length
        t2 = t1 ^ s2
        t3 = self.__u32_add(t2, s3)
        t4 = t3 ^ s4
       
        rot_t1, rot_t2, rot_t3, rot_t4 = (
            self.__js_left_rotate(t1, 9),
            self.__js_left_rotate(t2, 13),
            self.__js_left_rotate(t3, 17),
            self.__js_left_rotate(t4, 19),
        )

        p1 = self.__u32_add(rot_t1, rot_t3)
        p2 = rot_t2 ^ rot_t4
        p3 = self.__u32_add(rot_t3, p1)
        p4 = rot_t4 ^ p2
       
        return  p1.to_bytes(4, byteorder='little') + \
                p2.to_bytes(4, byteorder='little') + \
                p3.to_bytes(4, byteorder='little') + \
                p4.to_bytes(4, byteorder='little')

    
    
    def __encrypt_headers_x3(self, cookie_a1: str, cookie_loadts: int, uri: str="", params: dict = None, data: dict = None) -> str:

        if params:
            query_string = urllib.parse.urlencode(params).replace('%2C', ',')
            uri = f"{uri}?{query_string}"
        md5_url_params = hashlib.md5(uri.encode()).hexdigest()

        if data is not None:
            data_str = json.dumps(data, separators=(",", ":"))
            uri = uri + data_str

        md5_url_params_data = hashlib.md5(uri.encode()).hexdigest()
        encrypt_part1_4 = [121, 104, 96, 41]    # 固定

        random_num = int(random.random() * 4294967295)
        encrypt_part2_4 = list(random_num.to_bytes(4, byteorder='little'))

        timestamp = int(time.time() * 1000)
        encrypt_part3_8 = list(timestamp.to_bytes(8, byteorder='little'))

        encrypt_part4_8 = list(cookie_loadts.to_bytes(8, byteorder='little'))

        # 随机值1-99
        num = int(random.random() * 99) + 1
        encrypt_part5_4 = list(num.to_bytes(4, byteorder='little'))

        # Object.getOwnPropertyNames(window) # window对象属性数量
        num = 1352
        encrypt_part6_4 = list(num.to_bytes(4, byteorder='little'))

        # 拼接后uri的长度
        num = len(uri.encode("utf-8"))
        encrypt_part7_4 = list(num.to_bytes(4, byteorder='little'))

        encrypt_part8_8 = [b ^ (random_num & 255) for b in list(bytes.fromhex(md5_url_params_data))][0:8]
        byte_array = list(cookie_a1.encode('utf-8'))
        encrypt_part9_53 = [len(byte_array)] + byte_array

        byte_array = list(self.__appID.encode('utf-8'))
        encrypt_part10_11 = [len(byte_array)] + byte_array

        encrypt_part11_16 = [1, (random_num & 255) ^ 115, 249, 65, 103, 103, 201, 181, 131, 99, 94, 7, 68, 250, 132, 21]    # 固定

        encrypt_part12_4 = [2, 97, 51, 16]  # 固定 

        ts_and_md5_hash = list(self.__diy_hasher(encrypt_part3_8 + list(bytes.fromhex(md5_url_params))))
        encrypt_part13_16 = [i ^ (random_num & 255) for i in ts_and_md5_hash] 


        encrypt_144_old = encrypt_part1_4 + \
                            encrypt_part2_4 + \
                            encrypt_part3_8 + \
                            encrypt_part4_8 + \
                            encrypt_part5_4 + \
                            encrypt_part6_4 + \
                            encrypt_part7_4 + \
                            encrypt_part8_8 + \
                            encrypt_part9_53 + \
                            encrypt_part10_11 + \
                            encrypt_part11_16 + \
                            encrypt_part12_4 + \
                            encrypt_part13_16
        # 加密
        encrypt_144_new = [i^j for i, j in zip(encrypt_144_old, self.__xorkey)]
        encoded_str = self.__x3_prefix + b64_encode(bytes(encrypt_144_new), self.__x3_base64_table)
        return encoded_str


    def encrypt_headers_xs(self, cookie_a1: str, cookie_loadts: int, uri: str="", params: dict = None, data: dict = None) -> str:
        """
        Args:
            cookie_a1: Cookie中的a1值
            cookie_loadts: Cookie中的loadts(请求网页的时间戳)
            uri: 请求的url路径，例如 "/api/sns/web/v1/homefeed"
            params: get请求参数字典
            data: post请求数据字典
        Returns:
            str: 加密后的X-S字符串，格式为 "XYS_XXXXXXXXXXXXXXXXX"
        """
        
        p = {
            'x0' : self.__language_version,
            'x1' : self.__appID,
            'x2' : self.__os_system,
            'x3' : self.__encrypt_headers_x3(cookie_a1, cookie_loadts, uri, params, data),
            'x4' : "" if data is None else "object"
        }
        p_base64_encoded = b64_encode(
            encode_utf8(
                    urllib.parse.quote(
                        json.dumps(p, separators=(",", ":")), safe="-_.!~*'()")
                )
            , self.__base64_table)
        return "XYS_" + p_base64_encoded 

