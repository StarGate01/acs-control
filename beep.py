#!/usr/bin/env python3

import argparse, time

from smartcard.scard import *
from smartcard.pcsc import *


# As per the ACR documentation
def EscapeCommand(code):
    return 0x310000 + (code * 4)

# Used as dwControlCode in SCardControl 
ACR_API_CTL_CODE = EscapeCommand(3500)

# Control command APDUs

CMD_GET_FW_VERSION = [ 0xE0, 0x00, 0x00, 0x18, 0x00 ]

def CMD_LED_CONTROL(red = 0, green = 1):
    red = 0x01 if red else 0x00
    green = 0x02 if green else 0x00
    return [ 0xE0, 0x00, 0x00, 0x29, 0x01, red | green ]

def CMD_BUZZER_CONTROL(milliseconds):
    return [ 0xE0, 0x00, 0x00, 0x28, 0x01, min(0xFF, milliseconds // 10) ]

# Helper to properly display HRESULT values
def HRESULT(value):
    hresult = value & 0xFFFFFFFF
    return f"0x{hresult:08X}"

# Exchange a command with the reader
def control(cmd):
    print(f"Sending command: {bytes(cmd).hex()} ... ", end="")
    res, response = SCardControl(card, ACR_API_CTL_CODE, cmd)
    if res != SCARD_S_SUCCESS:
        print(f"error: {HRESULT(res)}")
    else:
        print(f"success, response: {bytes(response).hex()}")


if __name__ == '__main__':
    # Parse commandlien argumetns
    parser = argparse.ArgumentParser(description = 'Test SCardControl')
    parser.add_argument('-l', '--list-readers', action='store_true', dest='listreaders', 
        help='list available PC/SC readers')
    parser.add_argument('-r', '--reader', nargs='?', dest='reader', type=int, 
        const=0, default=0, 
        required=False, help='index of the PC/SC reader to use (default: 0)')
    args = parser.parse_args()

    # Open PC/SC subsystem, the scope does not really matter
    res, context = SCardEstablishContext(SCARD_SCOPE_USER)
    if res != SCARD_S_SUCCESS:
        print(f"Error establishing PC/SC context: {HRESULT(res)}")
        exit(1)

    # Get list of available readers
    res, redlist = SCardListReaders(context, [])
    if res != SCARD_S_SUCCESS:
        print(f"Error listing readers: {HRESULT(res)}")
        exit(1)

    # Order list of readers and select specified reader
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

    # Connect to reader. Note that dwShareMode = SCARD_SHARE_DIRECT and dwPreferredProtocols = 0
    # is needed to establish a connection without requiring a card on the reader.
    # See also https://learn.microsoft.com/en-us/windows/win32/api/winscard/nf-winscard-scardconnecta :
    # [dwPreferredProtocols] may be zero only if dwShareMode is set to SCARD_SHARE_DIRECT. 
    # In this case, no protocol negotiation will be performed by the drivers  [...]
    res, card, _ = SCardConnect(context, red, SCARD_SHARE_DIRECT, 0)
    if res != SCARD_S_SUCCESS:
        print(f"Error connecting to reader {red}: {HRESULT(res)}")
        exit(1)

    # Test some sample commands
    control(CMD_GET_FW_VERSION)
    for i in range(3):
        control(CMD_BUZZER_CONTROL(100))
        control(CMD_LED_CONTROL(True, True))
        time.sleep(1)
        control(CMD_LED_CONTROL(True, False))
        time.sleep(1)
        control(CMD_LED_CONTROL(False, True))
        time.sleep(1)
        control(CMD_LED_CONTROL(False, False))
        time.sleep(1)
    
    # Close reader connection
    res = SCardDisconnect(card, SCARD_UNPOWER_CARD)
    if res != SCARD_S_SUCCESS:
        print(f"Error disconnecting from reader: {HRESULT(res)}")
        exit(1)