from typing import Dict, List, Tuple
from json import dumps, loads
import argparse
import subprocess
import time
import usb


KEYBOARD_NAME = 'MX Keys'
VID = 0x046d
PID = 0xc52b


GENERAL_MAPPINGS = [
    (0x7000000e6, 0x7000000e7),  # Swap right CMD with OPT
]

MX_KEYS_MAPPINGS = [
    (0x700000064, 0x700000035),  # Swap §/£ with `/~
]

DEFAULT_INTERVAL = 10

Mapping = Dict[str, int]


def _make_mapping(src: int, dst: int) -> Mapping:
    d: Mapping = dict()
    d['HIDKeyboardModifierMappingSrc'] = src
    d['HIDKeyboardModifierMappingDst'] = dst
    return d


def make_mapping(pair: Tuple[int, int]) -> List[Mapping]:
    a, b = pair
    return [_make_mapping(a, b), _make_mapping(b, a)]


def set_mappings(mappings: List[Mapping]):
    mappinging_dict: Dict[str, List[Mapping]] = dict()
    mappinging_dict['UserKeyMapping'] = mappings
    subprocess.Popen(args=['hidutil', 'property', '--set',
                           dumps(mappinging_dict)],
                     stdout=subprocess.PIPE).communicate()


def is_keyboard_connected_bt(name: str) -> bool:
    stdout, _ = subprocess.Popen(args=['system_profiler',
                                       'SPBluetoothDataType',
                                       '-json'],
                                 stdout=subprocess.PIPE).communicate()
    out = loads(stdout.decode())
    try:
        connected_devices = out['SPBluetoothDataType'][0]['device_connected']
        for device in connected_devices:
            if name in device:
                return True
    except KeyError:
        return False
    return False


def is_keyboard_connected_usb(vid: int, pid: int) -> bool:
    device: usb.Device | None = usb.core.find(idVendor=vid, idProduct=pid)
    if device is not None:
        return True
    return False


def is_keyboard_connected() -> bool:
    bt_conn = is_keyboard_connected_bt(KEYBOARD_NAME)
    usb_conn = is_keyboard_connected_usb(VID, PID)
    return bt_conn or usb_conn


def update_mapping(keyboard_connected: bool):
    print(f'update: {keyboard_connected=}')
    mappings: List[Mapping] = list()
    for x in GENERAL_MAPPINGS:
        mappings.extend(make_mapping(x))
    if keyboard_connected:
        for x in MX_KEYS_MAPPINGS:
            mappings.extend(make_mapping(x))

    set_mappings(mappings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interval', type=int, default=DEFAULT_INTERVAL)
    args = parser.parse_args()

    prev_connected = is_keyboard_connected()
    update_mapping(prev_connected)

    while True:
        time.sleep(args.interval)
        connected = is_keyboard_connected()
        if connected != prev_connected:
            update_mapping(connected)
            prev_connected = connected


if __name__ == '__main__':
    main()
