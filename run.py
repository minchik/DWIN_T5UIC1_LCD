#!/usr/bin/env python3
from dwinlcd import DWinLcd
import logging

logging.basicConfig(filename='/tmp/dwin_lcd.log', level=logging.DEBUG)

encoder_Pins = (26, 19)
button_Pin = 13
LCD_COM_Port = '/dev/ttyAMA0'
API_Key = 'XXXXXX'

DWINLCD = DWinLcd(
    LCD_COM_Port,
    encoder_Pins,
    button_Pin,
    API_Key
)