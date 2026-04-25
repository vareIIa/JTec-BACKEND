def _crc16_ccitt(data: str) -> int:
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def _field(id_: int, value: str) -> str:
    return f"{id_:02d}{len(value):02d}{value}"


def generate_pix_payload(
    pix_key: str,
    amount: float,
    merchant_name: str,
    merchant_city: str,
    txid: str = "***",
) -> str:
    gui = _field(0, "BR.GOV.BCB.PIX")
    key_field = _field(1, pix_key)
    mai = _field(26, gui + key_field)

    txid_clean = txid[:25].replace(" ", "")
    txid_sub = _field(5, txid_clean)
    additional = _field(62, txid_sub)

    amount_str = f"{amount:.2f}"
    name = merchant_name[:25]
    city = merchant_city[:15]

    payload = (
        _field(0, "01")
        + _field(1, "12")
        + mai
        + _field(52, "0000")
        + _field(53, "986")
        + _field(54, amount_str)
        + _field(58, "BR")
        + _field(59, name)
        + _field(60, city)
        + additional
        + "6304"
    )

    crc = _crc16_ccitt(payload)
    return payload + f"{crc:04X}"
