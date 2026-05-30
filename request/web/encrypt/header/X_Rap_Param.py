import random
import math
import time
import struct
import base64
import json
import string
from request.web.encrypt.config import xhs_config

from .x_rap_param_helper.serialize_fingerprint_payload import serialize_payload_from_dict, xxh32
from .x_rap_param_helper.fixed_block_cipher import encrypt_bytes_with_length, xor_repeating

ALPHABET = string.ascii_lowercase + string.digits



class XHS_XRapParam_Encrypt:
    """小红书 x-rap-param 加密实现类
    有意思 小红书web的巅峰之作     
    """
    
    def __init__(self):
        self._xrap_need_encrypt_urls = xhs_config.get('XRAP_ENCRYPT', 'XRAP_ENCRYPT_URL')

    @staticmethod
    def _rand_str(length: int) -> str:
        return "".join(random.choice(ALPHABET) for _ in range(length))

    @staticmethod
    def _build_fingerprint_payload(uri, data: dict = None, now_ms = 0) -> list[int]:
        """构建指纹数据的序列化载荷"""

        if uri.startswith('https:'):
            uri = uri[6:]

        if data is not None:
            data_str = json.dumps(data, separators=(",", ":"))
            uri = uri + data_str

        # 前推几毫秒now_ms
        now_ms = now_ms - random.randint(10, 100)

        fp = {
            "AnonymousReadyStateV1": 0,
            "BrowserUseV1": 0,
            "CDPV1": 0,
            "CefBrowserV1": 0,
            "ChromedriverV1": 0,
            "ChromedriverV2": 0,
            "ChromedriverV3": 0,
            "ChromedriverV4": 0,
            "CrawleeV1": 0,
            "DrissionAutomationV1": 0,
            "DrissionAutomationV2": 0,
            "DrissionRunV1": 0,
            "FieldAbnormal": "",
            # "FocusBaseTime": str(now_ms - random.randint(2_000, 15_000)),
            "FocusData": {
                "events": [
                    {
                        "type": 0,
                        "dt": 0
                    },
                    {
                        "type": 1,
                        "dt": 5621
                    }
                ]
            },
            "HpChannelClick": 0,
            "HpCreatorTabClick": 0,
            "HpFilterClick": 0,
            "HpIconCloseClick": 0,
            "HpIconInputClick": 0,
            "HpIconSearchClick": 0,
            "KeyboardData": "",
            # "MouseBaseTime": str(now_ms - random.randint(300, 3_000)),
            "MouseBaseX": 484,      # 鼠标起始位置
            "MouseBaseY": 121,
            "MouseData": {
                "events": [
                    {
                        "dx": 1,
                        "dy": 0,
                        "dt": 0,
                        "type": 235
                    },
                    {
                        "dx": 0,
                        "dy": 0,
                        "dt": 0,
                        "type": 1
                    },
                    {
                        "dx": 1,
                        "dy": -3,
                        "dt": 68,
                        "type": 239
                    },
                    {
                        "dx": -7,
                        "dy": -3,
                        "dt": 21,
                        "type": 1
                    },
                    {
                        "dx": -262,
                        "dy": -30,
                        "dt": 808,
                        "type": 156
                    },
                    {
                        "dx": -174,
                        "dy": -13,
                        "dt": 752,
                        "type": 2
                    }
                ]
            },
            "PhantomjsV1": 0,
            "PhantomjsV2": 0,
            "PlayWrightV1": 0,
            "PlayWrightV2": 0,
            "PlayWrightV3": 0,
            "PuppteerV1": 0,
            "RequestHash": xxh32(uri, seed=0),
            "SeleniumV1": 0,
            "SignCostTime": {
                "signCost": random.randint(10, 40), # 签名耗时
                "transformCost": -1
            },
            # "Timestamp": str(now_ms),
            "TouchData": "",
            "UndetectedChromeDriverV1": 0,
            "Uuid": "joiamkprgeyi238i",
            "VisibilityData": "",
            "WheelData": "",
            "WheelIsTrusted": 0,
            "WindowBaseHeight": 1106, # window.innerHeight
            # "WindowBaseTime": str(now_ms - random.randint(30_000, 20 * 60_000)),
            "WindowBaseWidth": 486, # window.innerWidth
            "WindowResizeData": "",
            # "Xorkeyverifyvalue": 548432130, # 这个值由其他字段计算得出，放在serialize_payload_from_dict函数里计算
            "isCodeBeautify": 0,
            "isStealthV1": 0,
            "stealthJs": 0
        }

        # 配置各类时间戳
        max_mouse_dt = max(e["dt"] for e in fp["MouseData"]["events"])
        max_focus_dt = max(e["dt"] for e in fp["FocusData"]["events"])

        fp.update({
            "Timestamp": str(now_ms),
            "MouseBaseTime": str(now_ms - max_mouse_dt - random.randint(50, 300)),
            "FocusBaseTime": str(now_ms - max_focus_dt - random.randint(100, 1000)),
            "WindowBaseTime": str(now_ms - random.randint(30_000, 20 * 60_000)),
        })

        # 这个位置有能力的自洽一下 滑动轨迹/窗口宽高/时间线  我这里随便写一点了
        payload = serialize_payload_from_dict(fp, mtime=int(now_ms // 1000))
        return payload


    def _build_header(self, meta: dict) -> bytes:
        return struct.pack(
            ">BBBBIIIIIIII",
            (meta["protocolVersion"] << 2) + 3,
            meta["headerLen"],
            meta["protocolCryptType"],
            meta["randomStrLength"],

            meta["protocolCryptVersion"],
            meta["keyLength"],
            meta["payloadLen"],
            meta["bodyhash"],
            meta["sdkVersion"],
            meta["bodyEncryTime"],
            meta["flags"],
            meta["trailerLen"]
        )


    def encrypt_headers_xrap_param(self, url:str, data:dict = None) -> str | None:
        if url not in self._xrap_need_encrypt_urls:
            return None

        finish_ts = int(time.time() * 1000) # 直接设置一个最终时间， 其他的时间戳都根据这个来减
        raw_payload = self._build_fingerprint_payload(url, data, finish_ts)
        aes_key = self._rand_str(16).encode("latin1")

        encrypted_aes_key = encrypt_bytes_with_length(aes_key)

        pre_encrypt = xor_repeating(raw_payload, aes_key)
        encrypted_payload = encrypt_bytes_with_length(pre_encrypt)

        random_string = self._rand_str(random.randint(4, 6))

        payload_body = list(random_string.encode("latin1")) + list(encrypted_aes_key) + list(encrypted_payload)
        header_meta = {
            "protocolVersion": 1,
            "headerLen": 36,
            "protocolCryptType": 1,
            "randomStrLength": len(random_string),

            "protocolCryptVersion": 1,
            "keyLength": len(encrypted_aes_key),
            "payloadLen": len(encrypted_payload),
            "bodyhash": xxh32(bytes(payload_body), seed=0),
            "sdkVersion": 10300,
            "bodyEncryTime": random.randint(100, 500),
            "flags": 0,
            "trailerLen": 0,
        }
        header = self._build_header(header_meta)

        packet = list(header) + payload_body
        return base64.b64encode(bytes(packet)).decode()
    

if __name__ == "__main__":
    encryptor = XHS_XRapParam_Encrypt()
    url = "//edith.xiaohongshu.com/api/sns/web/v1/homefeed"
    data = {
        "cursor_score": "",
        "num": 20,
        "refresh_type": 1,
        "note_index": 13,
        "unread_begin_note_id": "",
        "unread_end_note_id": "",
        "unread_note_count": 0,
        "category": "homefeed.cosmetics_v3",
        "search_key": "",
        "need_num": 10,
        "image_formats": [
            "jpg",
            "webp",
            "avif"
        ],
        "need_filter_image": False
    }
    encrypted_header = encryptor.encrypt_headers_xrap_param(url, data)
    print("Encrypted x-rap-param header:", encrypted_header)