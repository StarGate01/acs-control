#!/usr/bin/env python3

import argparse

from smartcard.System import readers
from smartcard.scard import *
from smartcard.pcsc import *


def EscapeCommand(code):
    return 0x310000 + (code * 4)

ACR_API_CTL_CODE = 0x310000 + 3500*4 # EscapeCommand(3500)


CMD_GET_FW_VERSION = [ 0xE0, 0x00, 0x00, 0x18, 0x00 ]

def CMD_LED_CONTROL(red = 0, green = 1):
    red = 0x01 if red else 0x00
    green = 0x02 if green else 0x00
    return [ 0xE0, 0x00, 0x00, 0x29, 0x01, red | green ]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Test SCardControl')
    parser.add_argument('-l', '--list-readers', action='store_true', dest='listreaders', 
        help='list available PC/SC readers')
    parser.add_argument('-r', '--reader', nargs='?', dest='reader', type=int, 
        const=0, default=0, 
        required=False, help='index of the PC/SC reader to use (default: 0)')
    args = parser.parse_args()

    # Get list of available readers and select specified one

    res, context = SCardEstablishContext(SCARD_SCOPE_USER)
    if res != SCARD_S_SUCCESS:
        print(f"Error establishing PC/SC context: {res}")
        exit(1)

    res, redlist = SCardListReaders(context, [])
    if res != SCARD_S_SUCCESS:
        print(f"Error listing readers: {res}")
        exit(1)

    redlist.sort(key=str)
    if(args.listreaders):
        if(len(redlist) == 0):
            print('warning: No PC/SC readers found')
        else:
            print('info: Available PC/SC readers (' + str(len(redlist)) + '):')
            for i, reader in enumerate(redlist):
                print(str(i) + ': ' + str(reader))
        exit(0)

    if(len(redlist) == 0):
        print('error: No PC/SC readers found')
        exit(1)

    if(args.reader < 0 or args.reader >= len(redlist)):
        print('error: Specified reader index is out of range')
        exit(1)
    red = redlist[args.reader]
    print('info: Using reader ' + str(args.reader) + ': ' + str(red))

    # Connect and control reader

    res, card, _ = SCardConnect(context, red, SCARD_SHARE_DIRECT, SCARD_PROTOCOL_T0| SCARD_PROTOCOL_T1)
    if res != SCARD_S_SUCCESS:
        print(f"Error connecting to reader {red}: {res}")
        exit(1)

    #cmd = CMD_LED_CONTROL(True, False)
    cmd = CMD_GET_FW_VERSION
    res, response = SCardControl(card, ACR_API_CTL_CODE, cmd)
    if res != SCARD_S_SUCCESS:
        print(f"Error sending command: {bytes(cmd).hex()}: {res}")
    else:
        print(f"Success sensing command: {bytes(cmd).hex()}, response: {bytes(response).hex()}")

    res = SCardDisconnect(card, SCARD_UNPOWER_CARD)
    if res != SCARD_S_SUCCESS:
        print(f"Error disconnecting from reader: {res}")
        exit(1)