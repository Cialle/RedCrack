from __future__ import annotations

import json
from importlib import resources
from typing import Iterable


def _u32(value: int) -> int:
    return value & 0xFFFFFFFF


def _to_bytes(data: bytes | bytearray | str | Iterable[int]) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return data.encode("latin1")
    return bytes(x & 0xFF for x in data)


def _load_fixed_cipher_tables() -> tuple[list[list[int]], list[list[int]]]:
    table_text = resources.files(__package__).joinpath("fixed_cipher_tables.json").read_text(
        encoding="utf-8"
    )
    data = json.loads(table_text)
    round_keys = [[_u32(x) for x in row] for row in data["roundKeys"]]
    tables = [[_u32(x) for x in row] for row in data["tables"]]
    return round_keys, tables


ROUND_KEYS, TABLES = _load_fixed_cipher_tables()


def xor_repeating(data: bytes | bytearray | str | Iterable[int], key: bytes | bytearray | str | Iterable[int]) -> bytes:
    data_bytes = _to_bytes(data)
    key_bytes = _to_bytes(key)

    if len(data_bytes) == 0:
        return b""
    if len(data_bytes) < len(key_bytes):
        raise ValueError("error7")

    return bytes(value ^ key_bytes[index % len(key_bytes)] for index, value in enumerate(data_bytes))


def encrypt_bytes_with_length(data: bytes | bytearray | str | Iterable[int]) -> bytes:
    data_bytes = _to_bytes(data)
    blocks = (len(data_bytes) + 15) // 16
    out = bytearray()

    for block_index in range(blocks):
        block = data_bytes[block_index * 16 : block_index * 16 + 16]
        block = block + b"\x00" * (16 - len(block))

        state = [0, 0, 0, 0]
        for col in range(4):
            offset = col << 2
            word = (
                (block[offset] << 24)
                | (block[offset + 1] << 16)
                | (block[offset + 2] << 8)
                | block[offset + 3]
            )
            state[col] = _u32(word ^ ROUND_KEYS[0][col])

        for round_index in range(1, 10):
            next_state = [0, 0, 0, 0]
            for col in range(4):
                next_state[col] = _u32(
                    TABLES[0][(state[col] >> 24) & 0xFF]
                    ^ TABLES[1][(state[(col + 1) & 3] >> 16) & 0xFF]
                    ^ TABLES[2][(state[(col + 2) & 3] >> 8) & 0xFF]
                    ^ TABLES[3][state[(col + 3) & 3] & 0xFF]
                    ^ ROUND_KEYS[round_index][col]
                )
            state = next_state

        sbox = TABLES[4]
        final_round = ROUND_KEYS[10]
        final_block = bytearray(16)

        for col in range(4):
            key = final_round[col]
            base = col << 2
            final_block[base] = (sbox[(state[col] >> 24) & 0xFF] ^ (key >> 24)) & 0xFF
            final_block[base + 1] = (
                sbox[(state[(col + 1) & 3] >> 16) & 0xFF] ^ (key >> 16)
            ) & 0xFF
            final_block[base + 2] = (
                sbox[(state[(col + 2) & 3] >> 8) & 0xFF] ^ (key >> 8)
            ) & 0xFF
            final_block[base + 3] = (sbox[state[(col + 3) & 3] & 0xFF] ^ key) & 0xFF

        out.extend(final_block)

    out.extend(len(data_bytes).to_bytes(4, "big"))
    return bytes(out)

