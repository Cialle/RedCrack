import struct
from typing import Any, Callable

import xxhash

from .fflate_py import gzip_sync

VAR88 = "dc9cf1d927716ce4e2282c04a4d79d778c34ac7d8642496ab2a2ea2de0b5969b41874b79da271796784ca77cacb7a001ac425df6f2864375b7c04474443ba2ff441e162e24b33181561a057d9f12859d056ff9c8aabe50cd8082b204189039c844973347fd57aa26e027531b10cd4c1d914bde1bb294814309a86dd604e507f7"

ORDER = [
    "Timestamp", "Xorkeyverifyvalue", "Uuid", "RequestHash",
    "PhantomjsV1", "PhantomjsV2", "ChromedriverV1", "ChromedriverV2", "ChromedriverV3", "ChromedriverV4",
    "CDPV1", "UndetectedChromeDriverV1", "PlayWrightV1", "PlayWrightV2", "PlayWrightV3",
    "CrawleeV1", "CefBrowserV1", "PuppteerV1", "SeleniumV1", "BrowserUseV1",
    "DrissionRunV1", "AnonymousReadyStateV1", "DrissionAutomationV1", "DrissionAutomationV2",
    "FieldAbnormal", "isStealthV1", "isCodeBeautify", "stealthJs",
    "MouseBaseX", "MouseBaseY", "MouseBaseTime", "MouseData",
    "TouchData", "KeyboardData", "WheelData", "FocusBaseTime", "FocusData", "VisibilityData",
    "WindowBaseWidth", "WindowBaseHeight", "WindowBaseTime", "WindowResizeData",
    "WheelIsTrusted", "SignCostTime",
    "HpIconCloseClick", "HpIconSearchClick", "HpIconInputClick", "HpChannelClick", "HpFilterClick", "HpCreatorTabClick",
]

TAG_ID = {
    "Timestamp": 1000, "Xorkeyverifyvalue": 1001, "Uuid": 1002, "RequestHash": 1003,
    "PhantomjsV1": 1051, "PhantomjsV2": 1052, "ChromedriverV1": 1053, "ChromedriverV2": 1054,
    "ChromedriverV3": 1055, "ChromedriverV4": 1056, "CDPV1": 1057, "UndetectedChromeDriverV1": 1058,
    "PlayWrightV1": 1059, "PlayWrightV2": 1060, "PlayWrightV3": 1061, "CrawleeV1": 1062,
    "CefBrowserV1": 1063, "PuppteerV1": 1064, "SeleniumV1": 1065, "DrissionRunV1": 1066,
    "AnonymousReadyStateV1": 1067, "DrissionAutomationV1": 1068, "DrissionAutomationV2": 1069,
    "BrowserUseV1": 1070, "isStealthV1": 1071, "isCodeBeautify": 1072, "stealthJs": 1073,
    "MouseBaseX": 1075, "MouseBaseY": 1076, "MouseBaseTime": 1077, "MouseData": 1078,
    "TouchData": 1082, "KeyboardData": 1084, "WheelData": 1088, "FocusBaseTime": 1089,
    "FocusData": 1090, "SignCostTime": 1091, "WindowBaseWidth": 1092, "WindowResizeData": 1093,
    "WindowBaseHeight": 1094, "WindowBaseTime": 1095, "WheelIsTrusted": 1096, "VisibilityData": 1097,
    "FieldAbnormal": 1100, "HpIconCloseClick": 1151, "HpIconSearchClick": 1152, "HpIconInputClick": 1153,
    "HpChannelClick": 1154, "HpFilterClick": 1155, "HpCreatorTabClick": 1156,
}

TYPE_BY_NAME = {
    "Timestamp": "u64", "Xorkeyverifyvalue": "u32", "Uuid": "bytes", "RequestHash": "u32",
    "MouseBaseX": "u32", "MouseBaseY": "u32", "MouseBaseTime": "u64", "MouseData": "bytes",
    "TouchData": "bytes", "KeyboardData": "bytes", "WheelData": "bytes",
    "FocusBaseTime": "u64", "FocusData": "bytes", "VisibilityData": "bytes",
    "WindowBaseWidth": "u32", "WindowResizeData": "bytes", "WindowBaseHeight": "u32",
    "WindowBaseTime": "u64", "SignCostTime": "bytes", "FieldAbnormal": "bytes",
}

INT_PACK = {
    "u8": (">HB", 0xFF),
    "u16": (">HH", 0xFFFF),
    "u32": (">HI", 0xFFFFFFFF),
    "u64": (">HQ", 0xFFFFFFFFFFFFFFFF),
}
    
def to_bytes(value: Any) -> bytes:
    """普通 bytes 字段转换：空值、bytes、list[int]、hex 字符串、普通字符串。"""

    if value is None:
        return b""

    if isinstance(value, (bytes, bytearray, list)):
        return bytes(value)

    if isinstance(value, str):
        return value.encode("latin1")

    raise TypeError(f"unsupported bytes value: {type(value)!r}")


def pack_mouse_events(value: dict[str, Any]) -> bytes:
    return b"".join(
        struct.pack(
            ">hhHB",
            int(e.get("dx", e.get("deltaX", 0))),
            int(e.get("dy", e.get("deltaY", 0))),
            int(e.get("dt", e.get("deltaTime", 0))) & 0xFFFF,
            int(e.get("type", e.get("eventType", 0))) & 0xFF,
        )
        for e in value.get("events", [])
    )


def pack_focus_events(value: dict[str, Any]) -> bytes:
    return b"".join(
        struct.pack(
            ">BH",
            int(e.get("type", e.get("eventType", 0))) & 0xFF,
            int(e.get("dt", e.get("deltaTime", 0))) & 0xFFFF,
        )
        for e in value.get("events", [])
    )


def pack_sign_cost(value: dict[str, Any]) -> bytes:
    return struct.pack(">Hh", int(value["signCost"]) & 0xFFFF, int(value["transformCost"]))


SPECIAL_BYTES_PACKER: dict[str, Callable[[dict[str, Any]], bytes]] = {
    "MouseData": pack_mouse_events,
    "FocusData": pack_focus_events,
    "SignCostTime": pack_sign_cost,
}


def pack_bytes_field(name: str, value: Any) -> bytes:
    """按字段名转换 bytes 类型字段；特殊结构字段走专用编码，其他字段走普通转换。"""
    packer = SPECIAL_BYTES_PACKER.get(name)
    return packer(value) if packer and isinstance(value, dict) else to_bytes(value)


def xxh32(data: bytes | str, seed: int = 0) -> int:
    data = data.encode() if isinstance(data, str) else data
    return xxhash.xxh32(data, seed=seed).intdigest()


def xorkey_from_timestamp(timestamp: Any) -> bytes:
    timestamp_bytes = struct.pack(">Q", int(timestamp) & 0xFFFFFFFFFFFFFFFF)
    return VAR88[xxh32(timestamp_bytes) % len(VAR88)].encode("latin1")


def normalize_xorkey(xorkey: str | bytes | int | None, timestamp: Any) -> bytes:
    if xorkey is None:
        return xorkey_from_timestamp(timestamp)
    if isinstance(xorkey, str):
        return xorkey.encode("latin1")
    if isinstance(xorkey, int):
        return bytes([xorkey])
    return bytes(xorkey)


def xor_repeating(data: bytes, key: bytes) -> bytes:
    return bytes(byte ^ key[i % len(key)] for i, byte in enumerate(data))


def build_record(name: str, value: Any) -> bytes:
    tag = TAG_ID[name]
    typ = TYPE_BY_NAME.get(name, "u8")

    if typ == "bytes":
        raw = pack_bytes_field(name, value)
        return struct.pack(">HI", tag, len(raw)) + raw

    fmt, mask = INT_PACK[typ]
    return struct.pack(fmt, tag, int(value) & mask)


def validate_full_dict(values: dict[str, Any]) -> None:
    required = [name for name in ORDER if name != "Xorkeyverifyvalue"]
    missing = [name for name in required if name not in values]
    if missing:
        raise KeyError(f"missing required fields: {missing}")


def serialize_payload_from_dict(
    values: dict[str, Any],
    *,
    xorkey: str | bytes | int | None = None,
    mtime: int = 0,
    compresslevel: int = 6,
) -> list[int]:
    validate_full_dict(values)

    key = normalize_xorkey(xorkey, values["Timestamp"])

    values.update({
        "Xorkeyverifyvalue": xxh32(key),
    })

    records = [build_record(name, values[name]) for name in ORDER]
    payload = b"".join(records[:2] + [xor_repeating(record, key) for record in records[2:]])

    return list(gzip_sync(payload, level=compresslevel, mtime=mtime))