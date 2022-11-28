import time
import multitimer
import atexit
import logging

from encoder import Encoder
from RPi import GPIO

from printerInterface import PrinterData
from DWIN_Screen import T5UIC1_LCD


def current_milli_time():
    return round(time.time() * 1000)


class SelectT:
    now = 0
    last = 0

    def set(self, v):
        self.now = self.last = v

    def reset(self):
        self.set(0)

    def changed(self):
        c = (self.now != self.last)
        if c:
            self.last = self.now
            return c

    def dec(self):
        if self.now:
            self.now -= 1
        return self.changed()

    def inc(self, v):
        if self.now < (v - 1):
            self.now += 1
        else:
            self.now = (v - 1)
        return self.changed()


class DWinLcd:

    TROWS = 6
    MROWS = TROWS - 1  # Total rows, and other-than-Back
    TITLE_HEIGHT = 30  # Title bar height
    MLINE = 53         # Menu line height
    LBLX = 60          # Menu item label X
    MENU_CHR_W = 8
    STAT_CHR_W = 10

    dwin_abort_flag = False  # Flag to reset feedrate, return to Home

    MSG_STOP_PRINT = "Stop Print"
    MSG_PAUSE_PRINT = "Pausing..."

    DWIN_SCROLL_UP = 2
    DWIN_SCROLL_DOWN = 3

    select_page = SelectT()
    select_file = SelectT()
    select_print = SelectT()
    select_prepare = SelectT()

    select_control = SelectT()
    select_axis = SelectT()
    select_temp = SelectT()
    select_motion = SelectT()
    select_tune = SelectT()
    select_pla = SelectT()
    select_ABS = SelectT()

    index_file = MROWS
    index_prepare = MROWS
    index_control = MROWS
    index_leveling = MROWS
    index_tune = MROWS

    MainMenu = 0
    SelectFile = 1
    Prepare = 2
    Control = 3
    Leveling = 4
    PrintProcess = 5
    AxisMove = 6
    TemperatureID = 7
    Motion = 8
    Info = 9
    Tune = 10
    PLAPreheat = 11
    ABSPreheat = 12
    MaxSpeed = 13
    MaxSpeed_value = 14
    MaxAcceleration = 15
    MaxAcceleration_value = 16
    MaxJerk = 17
    MaxJerk_value = 18
    Step = 19
    Step_value = 20

    # Last Process ID
    Last_Prepare = 21

    # Back Process ID
    Back_Main = 22
    Back_Print = 23

    # Date variable ID
    Move_X = 24
    Move_Y = 25
    Move_Z = 26
    Extruder = 27
    ETemp = 28
    Homeoffset = 29
    BedTemp = 30
    FanSpeed = 31
    PrintSpeed = 32

    Print_window = 33
    Popup_Window = 34

    MINUNITMULT = 10

    ENCODER_DIFF_NO = 0  # no state
    ENCODER_DIFF_CW = 1  # clockwise rotation
    ENCODER_DIFF_CCW = 2  # counterclockwise rotation
    ENCODER_DIFF_ENTER = 3   # click
    ENCODER_WAIT = 80
    ENCODER_WAIT_ENTER = 300
    EncoderRateLimit = True

    dwin_zoffset = 0.0
    last_zoffset = 0.0

    # Picture ID
    Start_Process = 0
    Language_English = 1
    Language_Chinese = 2

    # ICON ID
    ICON = 0x09

    ICON_LOGO = 0
    ICON_Print_0 = 1
    ICON_Print_1 = 2
    ICON_Prepare_0 = 3
    ICON_Prepare_1 = 4
    ICON_Control_0 = 5
    ICON_Control_1 = 6
    ICON_Leveling_0 = 7
    ICON_Leveling_1 = 8
    ICON_HotendTemp = 9
    ICON_BedTemp = 10
    ICON_Speed = 11
    ICON_Zoffset = 12
    ICON_Back = 13
    ICON_File = 14
    ICON_PrintTime = 15
    ICON_RemainTime = 16
    ICON_Setup_0 = 17
    ICON_Setup_1 = 18
    ICON_Pause_0 = 19
    ICON_Pause_1 = 20
    ICON_Continue_0 = 21
    ICON_Continue_1 = 22
    ICON_Stop_0 = 23
    ICON_Stop_1 = 24
    ICON_Bar = 25
    ICON_More = 26

    ICON_Axis = 27
    ICON_CloseMotor = 28
    ICON_Homing = 29
    ICON_SetHome = 30
    ICON_PLAPreheat = 31
    ICON_ABSPreheat = 32
    ICON_Cool = 33
    ICON_Language = 34

    ICON_MoveX = 35
    ICON_MoveY = 36
    ICON_MoveZ = 37
    ICON_Extruder = 38

    ICON_Temperature = 40
    ICON_Motion = 41
    ICON_WriteEEPROM = 42
    ICON_ReadEEPROM = 43
    ICON_ResumeEEPROM = 44
    ICON_Info = 45

    ICON_SetEndTemp = 46
    ICON_SetBedTemp = 47
    ICON_FanSpeed = 48
    ICON_SetPLAPreheat = 49
    ICON_SetABSPreheat = 50

    ICON_MaxSpeed = 51
    ICON_MaxAccelerated = 52
    ICON_MaxJerk = 53
    ICON_Step = 54
    ICON_PrintSize = 55
    ICON_Version = 56
    ICON_Contact = 57
    ICON_StockConfiguraton = 58
    ICON_MaxSpeedX = 59
    ICON_MaxSpeedY = 60
    ICON_MaxSpeedZ = 61
    ICON_MaxSpeedE = 62
    ICON_MaxAccX = 63
    ICON_MaxAccY = 64
    ICON_MaxAccZ = 65
    ICON_MaxAccE = 66
    ICON_MaxSpeedJerkX = 67
    ICON_MaxSpeedJerkY = 68
    ICON_MaxSpeedJerkZ = 69
    ICON_MaxSpeedJerkE = 70
    ICON_StepX = 71
    ICON_StepY = 72
    ICON_StepZ = 73
    ICON_StepE = 74
    ICON_Setspeed = 75
    ICON_SetZOffset = 76
    ICON_Rectangle = 77
    ICON_BLTouch = 78
    ICON_TempTooLow = 79
    ICON_AutoLeveling = 80
    ICON_TempTooHigh = 81
    ICON_NoTips_C = 82
    ICON_NoTips_E = 83
    ICON_Continue_C = 84
    ICON_Continue_E = 85
    ICON_Cancel_C = 86
    ICON_Cancel_E = 87
    ICON_Confirm_C = 88
    ICON_Confirm_E = 89
    ICON_Info_0 = 90
    ICON_Info_1 = 91

    MENU_CHAR_LIMIT = 24
    STATUS_Y = 360

    MOTION_CASE_RATE = 1
    MOTION_CASE_ACCEL = 2
    MOTION_CASE_JERK = MOTION_CASE_ACCEL + 0
    MOTION_CASE_STEPS = MOTION_CASE_JERK + 1
    MOTION_CASE_TOTAL = MOTION_CASE_STEPS

    PREPARE_CASE_MOVE = 1
    PREPARE_CASE_DISA = 2
    PREPARE_CASE_HOME = 3
    PREPARE_CASE_ZOFF = PREPARE_CASE_HOME + 1
    PREPARE_CASE_PLA = PREPARE_CASE_ZOFF + 1
    PREPARE_CASE_ABS = PREPARE_CASE_PLA + 1
    PREPARE_CASE_COOL = PREPARE_CASE_ABS + 1
    PREPARE_CASE_LANG = PREPARE_CASE_COOL + 0
    PREPARE_CASE_TOTAL = PREPARE_CASE_LANG

    CONTROL_CASE_TEMP = 1
    CONTROL_CASE_MOVE = 2
    CONTROL_CASE_INFO = 3
    CONTROL_CASE_TOTAL = 3

    TUNE_CASE_SPEED = 1
    TUNE_CASE_TEMP = (TUNE_CASE_SPEED + 1)
    TUNE_CASE_BED = (TUNE_CASE_TEMP + 1)
    TUNE_CASE_FAN = (TUNE_CASE_BED + 0)
    TUNE_CASE_ZOFF = (TUNE_CASE_FAN + 1)
    TUNE_CASE_TOTAL = TUNE_CASE_ZOFF

    TEMP_CASE_TEMP = (0 + 1)
    TEMP_CASE_BED = (TEMP_CASE_TEMP + 1)
    TEMP_CASE_FAN = (TEMP_CASE_BED + 0)
    TEMP_CASE_PLA = (TEMP_CASE_FAN + 1)
    TEMP_CASE_ABS = (TEMP_CASE_PLA + 1)
    TEMP_CASE_TOTAL = TEMP_CASE_ABS

    PREHEAT_CASE_TEMP = (0 + 1)
    PREHEAT_CASE_BED = (PREHEAT_CASE_TEMP + 1)
    PREHEAT_CASE_FAN = (PREHEAT_CASE_BED + 0)
    PREHEAT_CASE_SAVE = (PREHEAT_CASE_FAN + 1)
    PREHEAT_CASE_TOTAL = PREHEAT_CASE_SAVE

    # Dwen serial screen initialization
    # Passing parameters: serial port number
    # DWIN screen uses serial port 1 to send
    def __init__(self, usart_x, encoder_pins, button_pin, octo_api_key):
        self.pd = PrinterData(octo_api_key)

        while self.pd.status is None:
            logging.debug("Waiting for printer status...")
            self.pd.init_webservices()
            time.sleep(5)

        GPIO.setmode(GPIO.BCM)
        self.lcd = T5UIC1_LCD(usart_x)
        self.hmi_show_boot("Loading...")
        self.encoder = Encoder(encoder_pins[0], encoder_pins[1])
        self.button_pin = button_pin
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.button_pin, GPIO.BOTH, callback=self.encoder_has_data)
        self.encoder.callback = self.encoder_has_data
        self.EncodeLast = 0
        self.EncodeMS = current_milli_time() + self.ENCODER_WAIT
        self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
        self.next_rts_update_ms = 0
        self.last_card_percent_value = 101

        self.check_key = self.MainMenu
        self.timer = multitimer.MultiTimer(interval=2, function=self.each_moment_update)
        self.hmi_show_boot()
        print("Boot looks good")
        print("Testing Web-services")
        self.pd.init_webservices()
        self.hmi_init()
        self.hmi_start_frame(False)

    def lcd_exit(self):
        print("Shutting down the LCD")
        self.lcd.JPG_ShowAndCache(0)
        self.lcd.Frame_SetDir(1)
        self.lcd.UpdateLCD()
        self.timer.stop()
        GPIO.remove_event_detect(self.button_pin)

    def m_base(self, l):
        return 49 + self.MLINE * l

    def hmi_set_language(self):
        self.lcd.JPG_CacheTo1(self.Language_English)

    def hmi_show_boot(self, msg=None):
        if msg:
            self.lcd.Draw_String(
                False, False, self.lcd.DWIN_FONT_STAT,
                self.lcd.Color_White, self.lcd.Color_Bg_Black,
                10, 50,
                msg
            )
        for t in range(0, 100, 2):
            self.lcd.ICON_Show(self.ICON, self.ICON_Bar, 15, 260)
            self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 15 + t * 242 / 100, 260, 257, 280)
            self.lcd.UpdateLCD()
            time.sleep(.020)

    def hmi_init(self):
        # HMI_SDCardInit()

        self.hmi_set_language()
        self.timer.start()
        atexit.register(self.lcd_exit)

    def hmi_start_frame(self, with_update):
        self.last_status = self.pd.status
        if self.pd.status == 'printing':
            self.goto_print_process()
        elif self.pd.status in ['operational', 'complete', 'standby', 'cancelled']:
            self.goto_main_menu()
        else:
            self.goto_main_menu()
        self.draw_status_area(with_update)

    def hmi_main_menu(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_page.inc(4):
                if self.select_page.now == 0:
                    self.icon_print()
                if self.select_page.now == 1:
                    self.icon_print()
                    self.icon_prepare()
                if self.select_page.now == 2:
                    self.icon_prepare()
                    self.icon_control()
                if self.select_page.now == 3:
                    self.icon_control()
                    if self.pd.HAS_ONE_STEP_LEVELING:
                        self.icon_leveling(True)
                    else:
                        self.icon_start_info(True)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_page.dec():
                if self.select_page.now == 0:
                    self.icon_print()
                    self.icon_prepare()
                elif self.select_page.now == 1:
                    self.icon_prepare()
                    self.icon_control()
                elif self.select_page.now == 2:
                    self.icon_control()
                    if self.pd.HAS_ONE_STEP_LEVELING:
                        self.icon_leveling(False)
                    else:
                        self.icon_start_info(False)
                elif self.select_page.now == 3:
                    if self.pd.HAS_ONE_STEP_LEVELING:
                        self.icon_leveling(True)
                    else:
                        self.icon_start_info(True)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_page.now == 0:  # Print File
                self.check_key = self.SelectFile
                self.draw_print_file_menu()
            if self.select_page.now == 1:  # Prepare
                self.check_key = self.Prepare
                self.select_prepare.reset()
                self.index_prepare = self.MROWS
                self.draw_prepare_menu()
            if self.select_page.now == 2:  # Control
                self.check_key = self.Control
                self.select_control.reset()
                self.index_control = self.MROWS
                self.draw_control_menu()
            if self.select_page.now == 3:  # Leveling or Info
                if self.pd.HAS_ONE_STEP_LEVELING:
                    self.check_key = self.Leveling
                    self.HMI_Leveling()
                else:
                    self.check_key = self.Info
                    self.draw_info_menu()

        self.lcd.UpdateLCD()

    def hmi_select_file(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        full_cnt = len(self.pd.get_files(refresh=True))

        if encoder_diff_state == self.ENCODER_DIFF_CW and full_cnt:
            if self.select_file.inc(1 + full_cnt):
                item_num = self.select_file.now - 1  # -1 for "Back"
                # Cursor past the bottom
                if self.select_file.now > self.MROWS and self.select_file.now > self.index_file:
                    self.index_file = self.select_file.now  # New bottom line
                    self.scroll_menu(self.DWIN_SCROLL_UP)
                    self.draw_sd_item(item_num, self.MROWS)  # Draw and init the shift name
                else:
                    self.move_highlight(1, self.select_file.now + self.MROWS - self.index_file)  # Just move highlight
        elif encoder_diff_state == self.ENCODER_DIFF_CCW and full_cnt:
            if self.select_file.dec():
                item_num = self.select_file.now - 1  # -1 for "Back"
                if self.select_file.now < self.index_file - self.MROWS:  # Cursor past the top
                    self.index_file -= 1  # New bottom line
                    self.scroll_menu(self.DWIN_SCROLL_DOWN)
                    if self.index_file == self.MROWS:
                        self.draw_back_first()
                    else:
                        self.draw_sd_item(item_num, 0)  # Draw the item (and init shift name)
                else:
                    self.move_highlight(-1, self.select_file.now + self.MROWS - self.index_file)  # Just move highlight
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_file.now == 0:  # Back
                self.select_page.set(0)
                self.goto_main_menu()
            else:
                filenum = self.select_file.now - 1
                # Reset highlight for next entry
                self.select_print.reset()
                self.select_file.reset()

                # // Start choice and print SD file
                self.pd.HMI_flag.heat_flag = True
                self.pd.HMI_flag.print_finish = False
                self.pd.HMI_ValueStruct.show_mode = 0

                self.pd.open_and_print_file(filenum)
                self.goto_print_process()

        self.lcd.UpdateLCD()

    def hmi_prepare(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_prepare.inc(1 + self.PREPARE_CASE_TOTAL):
                if self.select_prepare.now > self.MROWS and self.select_prepare.now > self.index_prepare:
                    self.index_prepare = self.select_prepare.now

                    # Scroll up and draw a blank bottom line
                    self.scroll_menu(self.DWIN_SCROLL_UP)
                    self.draw_menu_icon(self.MROWS, self.ICON_Axis + self.select_prepare.now - 1)

                    # Draw "More" icon for sub-menus
                    if self.index_prepare < 7:
                        self.draw_more_icon(self.MROWS - self.index_prepare + 1)

                    if self.pd.HAS_HOTEND:
                        if self.index_prepare == self.PREPARE_CASE_ABS:
                            self.item_prepare_abs(self.MROWS)
                    if self.pd.HAS_PREHEAT:
                        if self.index_prepare == self.PREPARE_CASE_COOL:
                            self.item_prepare_cool(self.MROWS)
                else:
                    self.move_highlight(1, self.select_prepare.now + self.MROWS - self.index_prepare)

        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_prepare.dec():
                if self.select_prepare.now < self.index_prepare - self.MROWS:
                    self.index_prepare -= 1
                    self.scroll_menu(self.DWIN_SCROLL_DOWN)

                    if self.index_prepare == self.MROWS:
                        self.draw_back_first()
                    else:
                        self.draw_menu_line(0, self.ICON_Axis + self.select_prepare.now - 1)

                    if self.index_prepare < 7:
                        self.draw_more_icon(self.MROWS - self.index_prepare + 1)

                    if self.index_prepare == 6:
                        self.item_prepare_move(0)
                    elif self.index_prepare == 7:
                        self.item_prepare_disable(0)
                    elif self.index_prepare == 8:
                        self.item_prepare_home(0)
                else:
                    self.move_highlight(-1, self.select_prepare.now + self.MROWS - self.index_prepare)

        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_prepare.now == 0:  # Back
                self.select_page.set(1)
                self.goto_main_menu()

            elif self.select_prepare.now == self.PREPARE_CASE_MOVE:  # Axis move
                self.check_key = self.AxisMove
                self.select_axis.reset()
                self.draw_move_menu()
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 1, 216, self.m_base(1), self.pd.current_position.x * self.MINUNITMULT
                )
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 1, 216, self.m_base(2), self.pd.current_position.y * self.MINUNITMULT
                )
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 1, 216, self.m_base(3), self.pd.current_position.z * self.MINUNITMULT
                )
                self.pd.send_g_code("G92 E0")
                self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale = 0
                self.lcd.Draw_Signed_Float(self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216, self.m_base(4), 0)
            elif self.select_prepare.now == self.PREPARE_CASE_DISA:  # Disable steppers
                self.pd.send_g_code("M84")
            elif self.select_prepare.now == self.PREPARE_CASE_HOME:  # Homing
                self.check_key = self.Last_Prepare
                self.index_prepare = self.MROWS
                self.pd.current_position.homing()
                self.pd.HMI_flag.home_flag = True
                self.popup_window_home()
                self.pd.send_g_code("G28")
            elif self.select_prepare.now == self.PREPARE_CASE_ZOFF:  # Z-offset
                self.check_key = self.Homeoffset
                if self.pd.HAS_BED_PROBE:
                    self.pd.probe_calibrate()

                self.pd.HMI_ValueStruct.show_mode = -4

                self.lcd.Draw_Signed_Float(
                    self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
                    self.m_base(self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare),
                    self.pd.HMI_ValueStruct.offset_value
                )
                self.EncoderRateLimit = False

            elif self.select_prepare.now == self.PREPARE_CASE_PLA:  # PLA preheat
                self.pd.preheat("PLA")

            elif self.select_prepare.now == self.PREPARE_CASE_ABS:  # ABS preheat
                self.pd.preheat("ABS")

            elif self.select_prepare.now == self.PREPARE_CASE_COOL:  # Cool
                if self.pd.HAS_FAN:
                    self.pd.zero_fan_speeds()
                self.pd.disable_all_heaters()

            elif self.select_prepare.now == self.PREPARE_CASE_LANG:  # Toggle Language
                self.HMI_ToggleLanguage()
                self.draw_prepare_menu()
        self.lcd.UpdateLCD()

    def hmi_control(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_control.inc(1 + self.CONTROL_CASE_TOTAL):
                if self.select_control.now > self.MROWS and self.select_control.now > self.index_control:
                    self.index_control = self.select_control.now
                    self.scroll_menu(self.DWIN_SCROLL_UP)
                    self.draw_menu_icon(self.MROWS, self.ICON_Temperature + self.index_control - 1)
                    self.draw_more_icon(self.CONTROL_CASE_TEMP + self.MROWS - self.index_control)  # Temperature >
                    self.draw_more_icon(self.CONTROL_CASE_MOVE + self.MROWS - self.index_control)  # Motion >
                    if self.index_control > self.MROWS:
                        self.draw_more_icon(self.CONTROL_CASE_INFO + self.MROWS - self.index_control)  # Info >
                        self.lcd.Frame_AreaCopy(1, 0, 104, 24, 114, self.LBLX, self.m_base(self.CONTROL_CASE_INFO - 1))
                else:
                    self.move_highlight(1, self.select_control.now + self.MROWS - self.index_control)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_control.dec():
                if self.select_control.now < self.index_control - self.MROWS:
                    self.index_control -= 1
                    self.scroll_menu(self.DWIN_SCROLL_DOWN)
                    if self.index_control == self.MROWS:
                        self.draw_back_first()
                    else:
                        self.draw_menu_line(0, self.ICON_Temperature + self.select_control.now - 1)
                    self.draw_more_icon(0 + self.MROWS - self.index_control + 1)  # Temperature >
                    self.draw_more_icon(1 + self.MROWS - self.index_control + 1)  # Motion >
                else:
                    self.move_highlight(-1, self.select_control.now + self.MROWS - self.index_control)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_control.now == 0:  # Back
                self.select_page.set(2)
                self.goto_main_menu()
            if self.select_control.now == self.CONTROL_CASE_TEMP:  # Temperature
                self.check_key = self.TemperatureID
                self.pd.HMI_ValueStruct.show_mode = -1
                self.select_temp.reset()
                self.draw_temperature_menu()
            if self.select_control.now == self.CONTROL_CASE_MOVE:  # Motion
                self.check_key = self.Motion
                self.select_motion.reset()
                self.draw_motion_menu()
            if self.select_control.now == self.CONTROL_CASE_INFO:  # Info
                self.check_key = self.Info
                self.draw_info_menu()

        self.lcd.UpdateLCD()

    def hmi_info(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.pd.HAS_ONE_STEP_LEVELING:
                self.check_key = self.Control
                self.select_control.set(self.CONTROL_CASE_INFO)
                self.draw_control_menu()
            else:
                self.select_page.set(3)
                self.goto_main_menu()
        self.lcd.UpdateLCD()

    def hmi_printing(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if self.pd.HMI_flag.done_confirm_flag:
            if encoder_diff_state == self.ENCODER_DIFF_ENTER:
                self.pd.HMI_flag.done_confirm_flag = False
                self.dwin_abort_flag = True  # Reset feedrate, return to Home
            return

        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_print.inc(3):
                if self.select_print.now == 0:
                    self.icon_tune()
                elif self.select_print.now == 1:
                    self.icon_tune()
                    if self.pd.printing_is_paused():
                        self.icon_continue()
                    else:
                        self.icon_pause()
                elif self.select_print.now == 2:
                    if self.pd.printing_is_paused():
                        self.icon_continue()
                    else:
                        self.icon_pause()
                    self.icon_stop()
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_print.dec():
                if self.select_print.now == 0:
                    self.icon_tune()
                    if self.pd.printing_is_paused():
                        self.icon_continue()
                    else:
                        self.icon_pause()
                elif self.select_print.now == 1:
                    if self.pd.printing_is_paused():
                        self.icon_continue()
                    else:
                        self.icon_pause()
                    self.icon_stop()
                elif self.select_print.now == 2:
                    self.icon_stop()
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_print.now == 0:  # Tune
                self.check_key = self.Tune
                self.pd.HMI_ValueStruct.show_mode = 0
                self.select_tune.reset()
                self.index_tune = self.MROWS
                self.draw_tune_menu()
            elif self.select_print.now == 1:  # Pause
                if self.pd.HMI_flag.pause_flag:
                    self.icon_pause()
                    self.pd.resume_job()
                else:
                    self.pd.HMI_flag.select_flag = True
                    self.check_key = self.Print_window
                    self.popup_window_pause_or_stop()
            elif self.select_print.now == 2:  # Stop
                self.pd.HMI_flag.select_flag = True
                self.check_key = self.Print_window
                self.popup_window_pause_or_stop()
        self.lcd.UpdateLCD()

    # Pause and Stop window */
    def hmi_pause_or_stop(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if encoder_diff_state == self.ENCODER_DIFF_CW:
            self.draw_select_highlight(False)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.draw_select_highlight(True)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_print.now == 1:  # pause window
                if self.pd.HMI_flag.select_flag:
                    self.pd.HMI_flag.pause_action = True
                    self.icon_continue()
                    self.pd.pause_job()
                self.goto_print_process()
            elif self.select_print.now == 2:  # stop window
                if self.pd.HMI_flag.select_flag:
                    self.dwin_abort_flag = True  # Reset feedrate, return to Home
                    self.pd.cancel_job()
                    self.goto_main_menu()
                else:
                    self.goto_print_process()  # cancel stop
        self.lcd.UpdateLCD()

    # Tune  */
    def hmi_tune(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_tune.inc(1 + self.TUNE_CASE_TOTAL):
                if self.select_tune.now > self.MROWS and self.select_tune.now > self.index_tune:
                    self.index_tune = self.select_tune.now
                    self.scroll_menu(self.DWIN_SCROLL_UP)
                else:
                    self.move_highlight(1, self.select_tune.now + self.MROWS - self.index_tune)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_tune.dec():
                if self.select_tune.now < self.index_tune - self.MROWS:
                    self.index_tune -= 1
                    self.scroll_menu(self.DWIN_SCROLL_DOWN)
                    if self.index_tune == self.MROWS:
                        self.draw_back_first()
                else:
                    self.move_highlight(-1, self.select_tune.now + self.MROWS - self.index_tune)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_tune.now == 0:  # Back
                self.select_print.set(0)
                self.goto_print_process()
            elif self.select_tune.now == self.TUNE_CASE_SPEED:  # Print speed
                self.check_key = self.PrintSpeed
                self.pd.HMI_ValueStruct.print_speed = self.pd.feed_rate_percentage
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.TUNE_CASE_SPEED + self.MROWS - self.index_tune),
                    self.pd.feed_rate_percentage
                )
                self.EncoderRateLimit = False
            elif self.select_tune.now == self.TUNE_CASE_ZOFF:   # z offset
                self.check_key = self.Homeoffset
                self.lcd.Draw_Signed_Float(
                    self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
                    self.m_base(self.TUNE_CASE_ZOFF + self.MROWS - self.index_tune),
                    self.pd.HMI_ValueStruct.offset_value
                )

        self.lcd.UpdateLCD()

    def hmi_print_speed(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.print_speed += 1

        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.print_speed -= 1

        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.check_key = self.Tune
            self.pd.set_feed_rate(self.pd.HMI_ValueStruct.print_speed)

        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            3, 216, self.m_base(self.select_tune.now + self.MROWS - self.index_tune),
            self.pd.HMI_ValueStruct.print_speed
        )

    def hmi_axis_move(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if self.pd.PREVENT_COLD_EXTRUSION:
            # popup window resume
            if self.pd.HMI_flag.ETempTooLow_flag:
                if encoder_diff_state == self.ENCODER_DIFF_ENTER:
                    self.pd.HMI_flag.ETempTooLow_flag = False
                    self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale = 0
                    self.draw_move_menu()
                    self.lcd.Draw_FloatValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 1, 216, self.m_base(1),
                        self.pd.HMI_ValueStruct.Move_X_scale
                    )
                    self.lcd.Draw_FloatValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 1, 216, self.m_base(2),
                        self.pd.HMI_ValueStruct.Move_Y_scale
                    )
                    self.lcd.Draw_FloatValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 1, 216, self.m_base(3),
                        self.pd.HMI_ValueStruct.Move_Z_scale
                    )
                    self.lcd.Draw_Signed_Float(
                        self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216, self.m_base(4), 0
                    )
                    self.lcd.UpdateLCD()
                return
        # Avoid flicker by updating only the previous menu
        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_axis.inc(1 + 4):
                self.move_highlight(1, self.select_axis.now)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_axis.dec():
                self.move_highlight(-1, self.select_axis.now)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_axis.now == 0:  # Back
                self.check_key = self.Prepare
                self.select_prepare.set(1)
                self.index_prepare = self.MROWS
                self.draw_prepare_menu()

            elif self.select_axis.now == 1:  # axis move
                self.check_key = self.Move_X
                self.pd.HMI_ValueStruct.Move_X_scale = self.pd.current_position.x * self.MINUNITMULT
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 1, 216, self.m_base(1),
                    self.pd.HMI_ValueStruct.Move_X_scale
                )
                self.EncoderRateLimit = False
            elif self.select_axis.now == 2:  # Y axis move
                self.check_key = self.Move_Y
                self.pd.HMI_ValueStruct.Move_Y_scale = self.pd.current_position.y * self.MINUNITMULT
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 1, 216, self.m_base(2),
                    self.pd.HMI_ValueStruct.Move_Y_scale
                )
                self.EncoderRateLimit = False
            elif self.select_axis.now == 3:  # Z axis move
                self.check_key = self.Move_Z
                self.pd.HMI_ValueStruct.Move_Z_scale = self.pd.current_position.z * self.MINUNITMULT
                self.lcd.Draw_FloatValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 1, 216, self.m_base(3),
                    self.pd.HMI_ValueStruct.Move_Z_scale
                )
                self.EncoderRateLimit = False
            elif self.select_axis.now == 4:  # Extruder
                # window tips
                if self.pd.PREVENT_COLD_EXTRUSION:
                    if self.pd.thermal_manager['temp_hotend'][0]['celsius'] < self.pd.EXTRUDE_MIN_TEMP:
                        self.pd.HMI_flag.ETempTooLow_flag = True
                        self.popup_window_e_temp_too_low()
                        self.lcd.UpdateLCD()
                        return
                self.check_key = self.Extruder
                self.pd.HMI_ValueStruct.Move_E_scale = self.pd.current_position.e * self.MINUNITMULT
                self.lcd.Draw_Signed_Float(
                    self.lcd.font8x16, self.lcd.Select_Color, 3, 1, 216, self.m_base(4),
                    self.pd.HMI_ValueStruct.Move_E_scale
                )
                self.EncoderRateLimit = False
        self.lcd.UpdateLCD()

    def hmi_move_x(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.check_key = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.Draw_FloatValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 1, 216, self.m_base(1),
                self.pd.HMI_ValueStruct.Move_X_scale
            )
            self.pd.move_absolute('X', self.pd.current_position.x, 5000)
            self.lcd.UpdateLCD()
            return
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_X_scale += 1
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_X_scale -= 1

        if self.pd.HMI_ValueStruct.Move_X_scale < self.pd.X_MIN_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_X_scale = self.pd.X_MIN_POS * self.MINUNITMULT

        if self.pd.HMI_ValueStruct.Move_X_scale > self.pd.X_MAX_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_X_scale = self.pd.X_MAX_POS * self.MINUNITMULT

        self.pd.current_position.x = self.pd.HMI_ValueStruct.Move_X_scale / 10
        self.lcd.Draw_FloatValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
            3, 1, 216, self.m_base(1), self.pd.HMI_ValueStruct.Move_X_scale)
        self.lcd.UpdateLCD()

    def hmi_move_y(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.check_key = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.Draw_FloatValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 1, 216, self.m_base(2),
                self.pd.HMI_ValueStruct.Move_Y_scale
            )

            self.pd.move_absolute('Y', self.pd.current_position.y, 5000)
            self.lcd.UpdateLCD()
            return
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_Y_scale += 1
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_Y_scale -= 1

        if self.pd.HMI_ValueStruct.Move_Y_scale < self.pd.Y_MIN_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_Y_scale = self.pd.Y_MIN_POS * self.MINUNITMULT

        if self.pd.HMI_ValueStruct.Move_Y_scale > self.pd.Y_MAX_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_Y_scale = self.pd.Y_MAX_POS * self.MINUNITMULT

        self.pd.current_position.y = self.pd.HMI_ValueStruct.Move_Y_scale / 10
        self.lcd.Draw_FloatValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
            3, 1, 216, self.m_base(2), self.pd.HMI_ValueStruct.Move_Y_scale)
        self.lcd.UpdateLCD()

    def hmi_move_z(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.check_key = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.Draw_FloatValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 1, 216, self.m_base(3),
                self.pd.HMI_ValueStruct.Move_Z_scale
            )
            self.pd.move_absolute('Z', self.pd.current_position.z, 600)
            self.lcd.UpdateLCD()
            return
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_Z_scale += 1
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_Z_scale -= 1

        if self.pd.HMI_ValueStruct.Move_Z_scale < self.pd.Z_MIN_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_Z_scale = self.pd.Z_MIN_POS * self.MINUNITMULT

        if self.pd.HMI_ValueStruct.Move_Z_scale > self.pd.Z_MAX_POS * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_Z_scale = self.pd.Z_MAX_POS * self.MINUNITMULT

        self.pd.current_position.z = self.pd.HMI_ValueStruct.Move_Z_scale / 10
        self.lcd.Draw_FloatValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
            3, 1, 216, self.m_base(3), self.pd.HMI_ValueStruct.Move_Z_scale)
        self.lcd.UpdateLCD()

    def hmi_move_e(self):
        self.pd.last_E_scale = 0
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.check_key = self.AxisMove
            self.EncoderRateLimit = True
            self.pd.last_E_scale = self.pd.HMI_ValueStruct.Move_E_scale
            self.lcd.Draw_Signed_Float(
                self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216,
                self.m_base(4), self.pd.HMI_ValueStruct.Move_E_scale
            )
            self.pd.move_absolute('E', self.pd.current_position.e, 300)
            self.lcd.UpdateLCD()
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_E_scale += 1
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_E_scale -= 1

        if (self.pd.HMI_ValueStruct.Move_E_scale - self.pd.last_E_scale) > self.pd.EXTRUDE_MAXLENGTH * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_E_scale = self.pd.last_E_scale + self.pd.EXTRUDE_MAXLENGTH * self.MINUNITMULT
        elif (self.pd.last_E_scale - self.pd.HMI_ValueStruct.Move_E_scale) > \
                self.pd.EXTRUDE_MAXLENGTH * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_E_scale = self.pd.last_E_scale - self.pd.EXTRUDE_MAXLENGTH * self.MINUNITMULT
        self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale / 10
        self.lcd.Draw_Signed_Float(
            self.lcd.font8x16, self.lcd.Select_Color, 3, 1, 216, self.m_base(4), self.pd.HMI_ValueStruct.Move_E_scale
        )
        self.lcd.UpdateLCD()

    def hmi_temperature(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_temp.inc(1 + self.TEMP_CASE_TOTAL):
                self.move_highlight(1, self.select_temp.now)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_temp.dec():
                self.move_highlight(-1, self.select_temp.now)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_temp.now == 0:  # back
                self.check_key = self.Control
                self.select_control.set(1)
                self.index_control = self.MROWS
                self.draw_control_menu()
            elif self.select_temp.now == self.TEMP_CASE_TEMP:  # Nozzle temperature
                self.check_key = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.thermal_manager['temp_hotend'][0]['target']
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(1),
                    self.pd.thermal_manager['temp_hotend'][0]['target']
                )
                self.EncoderRateLimit = False
            elif self.select_temp.now == self.TEMP_CASE_BED:  # Bed temperature
                self.check_key = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.thermal_manager['temp_bed']['target']
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(2),
                    self.pd.thermal_manager['temp_bed']['target']
                )
                self.EncoderRateLimit = False
            elif self.select_temp.now == self.TEMP_CASE_FAN:  # Fan speed
                self.check_key = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.thermal_manager['fan_speed'][0]
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(3), self.pd.thermal_manager['fan_speed'][0]
                )
                self.EncoderRateLimit = False

            elif self.select_temp.now == self.TEMP_CASE_PLA:  # PLA preheat setting
                self.check_key = self.PLAPreheat
                self.select_pla.reset()
                self.pd.HMI_ValueStruct.show_mode = -2

                self.clear_main_window()
                self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "PLA Settings"
                self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_TEMP))
                self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_TEMP))
                # PLA nozzle temp
                self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 71, self.m_base(self.PREHEAT_CASE_TEMP))
                if self.pd.HAS_HEATED_BED:
                    self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_BED) + 3)
                    self.lcd.Frame_AreaCopy(
                        1, 240, 104, 264, 114, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_BED) + 3
                    )
                    # PLA bed temp
                    self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 54, self.m_base(self.PREHEAT_CASE_BED) + 3)
                if self.pd.HAS_FAN:
                    self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_FAN))
                    # PLA fan speed
                    self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_FAN))

                # Save PLA configuration
                self.lcd.Frame_AreaCopy(1, 97, 165, 229, 177, self.LBLX, self.m_base(self.PREHEAT_CASE_SAVE))

                self.draw_back_first()
                i = 1
                self.draw_menu_line(i, self.ICON_SetEndTemp)
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(i),
                    self.pd.material_preset[0].hotend_temp
                )
                if self.pd.HAS_HEATED_BED:
                    i += 1
                    self.draw_menu_line(i, self.ICON_SetBedTemp)
                    self.lcd.Draw_IntValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 216, self.m_base(i),
                        self.pd.material_preset[0].bed_temp
                    )
                if self.pd.HAS_FAN:
                    i += 1
                    self.draw_menu_line(i, self.ICON_FanSpeed)
                    self.lcd.Draw_IntValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 216, self.m_base(i),
                        self.pd.material_preset[0].fan_speed
                    )
                i += 1
                self.draw_menu_line(i, self.ICON_WriteEEPROM)
            elif self.select_temp.now == self.TEMP_CASE_ABS:  # ABS preheat setting
                self.check_key = self.ABSPreheat
                self.select_ABS.reset()
                self.pd.HMI_ValueStruct.show_mode = -3
                self.clear_main_window()
                self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "ABS Settings"
                self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_TEMP))
                self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_TEMP))
                self.lcd.Frame_AreaCopy(
                    1, 1, 89, 83, 101, self.LBLX + 71, self.m_base(self.PREHEAT_CASE_TEMP)
                )  # ABS nozzle temp
                if self.pd.HAS_HEATED_BED:
                    self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_BED) + 3)
                    self.lcd.Frame_AreaCopy(
                        1, 240, 104, 264, 114, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_BED) + 3
                    )
                    # ABS bed temp
                    self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 54, self.m_base(self.PREHEAT_CASE_BED) + 3)
                if self.pd.HAS_FAN:
                    self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.m_base(self.PREHEAT_CASE_FAN))
                    # ABS fan speed
                    self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX + 27, self.m_base(self.PREHEAT_CASE_FAN))

                self.lcd.Frame_AreaCopy(1, 97, 165, 229, 177, self.LBLX, self.m_base(self.PREHEAT_CASE_SAVE))
                # Save ABS configuration
                self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 33, self.m_base(self.PREHEAT_CASE_SAVE))

                self.draw_back_first()
                i = 1
                self.draw_menu_line(i, self.ICON_SetEndTemp)
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(i),
                    self.pd.material_preset[1].hotend_temp
                )
                if self.pd.HAS_HEATED_BED:
                    i += 1
                    self.draw_menu_line(i, self.ICON_SetBedTemp)
                    self.lcd.Draw_IntValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 216, self.m_base(i),
                        self.pd.material_preset[1].bed_temp
                    )
                if self.pd.HAS_FAN:
                    i += 1
                    self.draw_menu_line(i, self.ICON_FanSpeed)
                    self.lcd.Draw_IntValue(
                        True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                        3, 216, self.m_base(i),
                        self.pd.material_preset[1].fan_speed
                    )
                i += 1
                self.draw_menu_line(i, self.ICON_WriteEEPROM)

        self.lcd.UpdateLCD()

    def hmi_pla_preheat_setting(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        # Avoid flicker by updating only the previous menu
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_pla.inc(1 + self.PREHEAT_CASE_TOTAL):
                self.move_highlight(1, self.select_pla.now)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_pla.dec():
                self.move_highlight(-1, self.select_pla.now)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:

            if self.select_pla.now == 0:  # Back
                self.check_key = self.TemperatureID
                self.select_temp.now = self.TEMP_CASE_PLA
                self.pd.HMI_ValueStruct.show_mode = -1
                self.draw_temperature_menu()
            elif self.select_pla.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
                self.check_key = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[0].hotend_temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_TEMP),
                    self.pd.material_preset[0].hotend_temp
                )
                self.EncoderRateLimit = False
            elif self.select_pla.now == self.PREHEAT_CASE_BED:  # Bed temperature
                self.check_key = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[0].bed_temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_BED),
                    self.pd.material_preset[0].bed_temp
                )
                self.EncoderRateLimit = False
            elif self.select_pla.now == self.PREHEAT_CASE_FAN:  # Fan speed
                self.check_key = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[0].fan_speed
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_FAN),
                    self.pd.material_preset[0].fan_speed
                )
                self.EncoderRateLimit = False
            elif self.select_pla.now == self.PREHEAT_CASE_SAVE:  # Save PLA configuration
                success = self.pd.save_settings()
                self.hmi_audio_feedback(success)
        self.lcd.UpdateLCD()

    def hmi_abs_preheat_setting(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        # Avoid flicker by updating only the previous menu
        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_ABS.inc(1 + self.PREHEAT_CASE_TOTAL):
                self.move_highlight(1, self.select_ABS.now)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_ABS.dec():
                self.move_highlight(-1, self.select_ABS.now)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:

            if self.select_ABS.now == 0:  # Back
                self.check_key = self.TemperatureID
                self.select_temp.now = self.TEMP_CASE_ABS
                self.pd.HMI_ValueStruct.show_mode = -1
                self.draw_temperature_menu()

            elif self.select_ABS.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
                self.check_key = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[1].hotend_temp
                print(self.pd.HMI_ValueStruct.E_Temp)
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_TEMP),
                    self.pd.material_preset[1].hotend_temp
                )
                self.EncoderRateLimit = False
            elif self.select_ABS.now == self.PREHEAT_CASE_BED:  # Bed temperature
                self.check_key = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[1].bed_temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_BED),
                    self.pd.material_preset[1].bed_temp
                )
                self.EncoderRateLimit = False
            elif self.select_ABS.now == self.PREHEAT_CASE_FAN:  # Fan speed
                self.check_key = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[1].fan_speed
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
                    3, 216, self.m_base(self.PREHEAT_CASE_FAN),
                    self.pd.material_preset[1].fan_speed
                )
                self.EncoderRateLimit = False
            elif self.select_ABS.now == self.PREHEAT_CASE_SAVE:  # Save PLA configuration
                success = self.pd.save_settings()
                self.hmi_audio_feedback(success)
        self.lcd.UpdateLCD()

    def hmi_e_temp(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if self.pd.HMI_ValueStruct.show_mode == -1:
            temp_line = self.TEMP_CASE_TEMP
        elif self.pd.HMI_ValueStruct.show_mode == -2:
            temp_line = self.PREHEAT_CASE_TEMP
        elif self.pd.HMI_ValueStruct.show_mode == -3:
            temp_line = self.PREHEAT_CASE_TEMP
        else:
            temp_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

        if encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.EncoderRateLimit = True
            if self.pd.HMI_ValueStruct.show_mode == -1:  # temperature
                self.check_key = self.TemperatureID
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(temp_line),
                    self.pd.HMI_ValueStruct.E_Temp
                )
            elif self.pd.HMI_ValueStruct.show_mode == -2:
                self.check_key = self.PLAPreheat
                self.pd.material_preset[0].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(temp_line),
                    self.pd.material_preset[0].hotend_temp
                )
                return
            elif self.pd.HMI_ValueStruct.show_mode == -3:
                self.check_key = self.ABSPreheat
                self.pd.material_preset[1].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(temp_line),
                    self.pd.material_preset[1].hotend_temp
                )
                return
            else:  # tune
                self.check_key = self.Tune
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(temp_line),
                    self.pd.HMI_ValueStruct.E_Temp
                )
                self.pd.setTargetHotend(self.pd.HMI_ValueStruct.E_Temp, 0)
            return

        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.E_Temp += 1

        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.E_Temp -= 1

        # E_Temp limit
        if self.pd.HMI_ValueStruct.E_Temp > self.pd.MAX_E_TEMP:
            self.pd.HMI_ValueStruct.E_Temp = self.pd.MAX_E_TEMP
        if self.pd.HMI_ValueStruct.E_Temp < self.pd.MIN_E_TEMP:
            self.pd.HMI_ValueStruct.E_Temp = self.pd.MIN_E_TEMP
        # E_Temp value
        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
            3, 216, self.m_base(temp_line),
            self.pd.HMI_ValueStruct.E_Temp
        )

    def hmi_bed_temp(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

        if self.pd.HMI_ValueStruct.show_mode == -1:
            bed_line = self.TEMP_CASE_BED
        elif self.pd.HMI_ValueStruct.show_mode == -2:
            bed_line = self.PREHEAT_CASE_BED
        elif self.pd.HMI_ValueStruct.show_mode == -3:
            bed_line = self.PREHEAT_CASE_BED
        else:
            bed_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

        if encoder_diff_state == self.ENCODER_DIFF_ENTER:
            self.EncoderRateLimit = True
            if self.pd.HMI_ValueStruct.show_mode == -1:  # temperature
                self.check_key = self.TemperatureID
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(bed_line),
                    self.pd.HMI_ValueStruct.Bed_Temp
                )
            elif self.pd.HMI_ValueStruct.show_mode == -2:
                self.check_key = self.PLAPreheat
                self.pd.material_preset[0].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(bed_line),
                    self.pd.material_preset[0].bed_temp
                )
                return
            elif self.pd.HMI_ValueStruct.show_mode == -3:
                self.check_key = self.ABSPreheat
                self.pd.material_preset[1].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(bed_line),
                    self.pd.material_preset[1].bed_temp
                )
                return
            else:  # tune
                self.check_key = self.Tune
                self.lcd.Draw_IntValue(
                    True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                    3, 216, self.m_base(bed_line),
                    self.pd.HMI_ValueStruct.Bed_Temp
                )
                self.pd.setTargetHotend(self.pd.HMI_ValueStruct.Bed_Temp, 0)
            return

        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Bed_Temp += 1

        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Bed_Temp -= 1

        # Bed_Temp limit
        if self.pd.HMI_ValueStruct.Bed_Temp > self.pd.BED_MAX_TARGET:
            self.pd.HMI_ValueStruct.Bed_Temp = self.pd.BED_MAX_TARGET
        if self.pd.HMI_ValueStruct.Bed_Temp < self.pd.MIN_BED_TEMP:
            self.pd.HMI_ValueStruct.Bed_Temp = self.pd.MIN_BED_TEMP
        # Bed_Temp value
        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
            3, 216, self.m_base(bed_line),
            self.pd.HMI_ValueStruct.Bed_Temp
        )

# ---------------------Todo--------------------------------#

    def hmi_motion(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if encoder_diff_state == self.ENCODER_DIFF_CW:
            if self.select_motion.inc(1 + self.MOTION_CASE_TOTAL):
                self.move_highlight(1, self.select_motion.now)
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            if self.select_motion.dec():
                self.move_highlight(-1, self.select_motion.now)
        elif encoder_diff_state == self.ENCODER_DIFF_ENTER:
            if self.select_motion.now == 0:  # back
                self.check_key = self.Control
                self.select_control.set(self.CONTROL_CASE_MOVE)
                self.index_control = self.MROWS
                self.draw_control_menu()
        self.lcd.UpdateLCD()

    def hmi_z_offset(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return
        if self.pd.HMI_ValueStruct.show_mode == -4:
            zoff_line = self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare
        else:
            zoff_line = self.TUNE_CASE_ZOFF + self.MROWS - self.index_tune

        if encoder_diff_state == self.ENCODER_DIFF_ENTER:  # if (applyencoder(encoder_diffstate, offset_value))
            self.EncoderRateLimit = True
            if self.pd.HAS_BED_PROBE:
                self.pd.offset_z(self.dwin_zoffset)
            else:
                self.pd.set_z_offset(self.dwin_zoffset)  # manually set

            self.check_key = self.Prepare if self.pd.HMI_ValueStruct.show_mode == -4 else self.Tune
            self.lcd.Draw_Signed_Float(
                self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202, self.m_base(zoff_line),
                self.pd.HMI_ValueStruct.offset_value
            )

            self.lcd.UpdateLCD()
            return

        elif encoder_diff_state == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.offset_value += 1
        elif encoder_diff_state == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.offset_value -= 1

        if self.pd.HMI_ValueStruct.offset_value < self.pd.Z_PROBE_OFFSET_RANGE_MIN * 100:
            self.pd.HMI_ValueStruct.offset_value = self.pd.Z_PROBE_OFFSET_RANGE_MIN * 100
        elif self.pd.HMI_ValueStruct.offset_value > self.pd.Z_PROBE_OFFSET_RANGE_MAX * 100:
            self.pd.HMI_ValueStruct.offset_value = self.pd.Z_PROBE_OFFSET_RANGE_MAX * 100

        self.last_zoffset = self.dwin_zoffset
        self.dwin_zoffset = self.pd.HMI_ValueStruct.offset_value / 100.0
        if self.pd.HAS_BED_PROBE:
            self.pd.add_mm('Z', self.dwin_zoffset - self.last_zoffset)

        self.lcd.Draw_Signed_Float(
            self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
            self.m_base(zoff_line),
            self.pd.HMI_ValueStruct.offset_value
        )
        self.lcd.UpdateLCD()

    def hmi_max_speed(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_max_acceleration(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_max_jerk(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_step(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_max_feed_speed_xyze(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_max_acceleration_xyze(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_max_jerk_xyze(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    def hmi_step_xyze(self):
        encoder_diff_state = self.get_encoder_state()
        if encoder_diff_state == self.ENCODER_DIFF_NO:
            return

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def draw_status_area(self, with_update):
        #  Clear the bottom area of the screen
        self.lcd.Draw_Rectangle(
            1, self.lcd.Color_Bg_Black, 0, self.STATUS_Y, self.lcd.DWIN_WIDTH, self.lcd.DWIN_HEIGHT - 1
        )
        #
        #  Status Area
        #
        if self.pd.HAS_HOTEND:
            self.lcd.ICON_Show(self.ICON, self.ICON_HotendTemp, 13, 381)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.DWIN_FONT_STAT,
                self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 33, 382,
                self.pd.thermal_manager['temp_hotend'][0]['celsius']
            )
            self.lcd.Draw_String(
                False, False, self.lcd.DWIN_FONT_STAT,
                self.lcd.Color_White, self.lcd.Color_Bg_Black,
                33 + 3 * self.STAT_CHR_W + 5, 383,
                "/"
            )
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.DWIN_FONT_STAT,
                self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 33 + 4 * self.STAT_CHR_W + 6, 382,
                self.pd.thermal_manager['temp_hotend'][0]['target']
            )

        if self.pd.HOTENDS > 1:
            self.lcd.ICON_Show(self.ICON, self.ICON_HotendTemp, 13, 381)

        if self.pd.HAS_HEATED_BED:
            self.lcd.ICON_Show(self.ICON, self.ICON_BedTemp, 158, 381)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.DWIN_FONT_STAT, self.lcd.Color_White,
                self.lcd.Color_Bg_Black, 3, 178, 382,
                self.pd.thermal_manager['temp_bed']['celsius']
            )
            self.lcd.Draw_String(
                False, False, self.lcd.DWIN_FONT_STAT, self.lcd.Color_White,
                self.lcd.Color_Bg_Black, 178 + 3 * self.STAT_CHR_W + 5, 383,
                "/"
            )
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.DWIN_FONT_STAT,
                self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 178 + 4 * self.STAT_CHR_W + 6, 382,
                self.pd.thermal_manager['temp_bed']['target']
            )

        self.lcd.ICON_Show(self.ICON, self.ICON_Speed, 13, 429)
        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.DWIN_FONT_STAT,
            self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 33 + 2 * self.STAT_CHR_W, 429,
            self.pd.feed_rate_percentage
        )
        self.lcd.Draw_String(
            False, False, self.lcd.DWIN_FONT_STAT,
            self.lcd.Color_White, self.lcd.Color_Bg_Black, 33 + 5 * self.STAT_CHR_W + 2, 429,
            "%"
        )

        if self.pd.HAS_Z_OFFSET_ITEM:
            self.lcd.ICON_Show(self.ICON, self.ICON_Zoffset, 158, 428)
            self.lcd.Draw_Signed_Float(
                self.lcd.DWIN_FONT_STAT, self.lcd.Color_Bg_Black, 2, 2, 178, 429, self.pd.BABY_Z_VAR * 100
            )

        # if with_update:
        # 	self.lcd.UpdateLCD()
        # 	time.sleep(.005)

    def draw_title(self, title):
        self.lcd.Draw_String(
            False, False, self.lcd.DWIN_FONT_HEAD, self.lcd.Color_White, self.lcd.Color_Bg_Blue, 14, 4, title
        )

    def draw_popup_bkgd_105(self):
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Window, 14, 105, 258, 374)

    def draw_more_icon(self, line):
        self.lcd.ICON_Show(self.ICON, self.ICON_More, 226, self.m_base(line) - 3)

    def draw_menu_cursor(self, line):
        self.lcd.Draw_Rectangle(1, self.lcd.Rectangle_Color, 0, self.m_base(line) - 18, 14, self.m_base(line + 1) - 20)

    def draw_menu_icon(self, line, icon):
        self.lcd.ICON_Show(self.ICON, icon, 26, self.m_base(line) - 3)

    def draw_menu_line(self, line, icon=None, label=None):
        if label:
            self.lcd.Draw_String(
                False, False, self.lcd.font8x16, self.lcd.Color_White,
                self.lcd.Color_Bg_Black, self.LBLX, self.m_base(line) - 1, label
            )
        if icon:
            self.draw_menu_icon(line, icon)
        self.lcd.Draw_Line(self.lcd.Line_Color, 16, self.m_base(line) + 33, 256, self.m_base(line) + 34)

    # The "Back" label is always on the first line
    def draw_back_label(self):
        self.lcd.Frame_AreaCopy(1, 226, 179, 256, 189, self.LBLX, self.m_base(0))

    # Draw "Back" line at the top
    def draw_back_first(self, is_sel=True):
        self.draw_menu_line(0, self.ICON_Back)
        self.draw_back_label()
        if is_sel:
            self.draw_menu_cursor(0)

    def draw_move_en(self, line):
        self.lcd.Frame_AreaCopy(1, 69, 61, 102, 71, self.LBLX, line)  # "Move"

    def draw_max_en(self, line):
        self.lcd.Frame_AreaCopy(1, 245, 119, 269, 129, self.LBLX, line)  # "Max"

    def draw_max_accel_en(self, line):
        self.draw_max_en(line)
        self.lcd.Frame_AreaCopy(1, 1, 135, 79, 145, self.LBLX + 27, line)  # "Acceleration"

    def draw_speed_en(self, inset, line):
        self.lcd.Frame_AreaCopy(1, 184, 119, 224, 132, self.LBLX + inset, line)  # "Speed"

    def draw_jerk_en(self, line):
        self.lcd.Frame_AreaCopy(1, 64, 119, 106, 129, self.LBLX + 27, line)  # "Jerk"

    def draw_steps_per_mm(self, line):
        self.lcd.Frame_AreaCopy(1, 1, 151, 101, 161, self.LBLX, line)  # "Steps-per-mm"

    # Display an SD item
    def draw_sd_item(self, item, row=0):
        fl = self.pd.get_files()[item]
        self.draw_menu_line(row, self.ICON_File, fl)

    def draw_select_highlight(self, sel):
        self.pd.HMI_flag.select_flag = sel
        if sel:
            c1 = self.lcd.Select_Color
            c2 = self.lcd.Color_Bg_Window
        else:
            c1 = self.lcd.Color_Bg_Window
            c2 = self.lcd.Select_Color
        self.lcd.Draw_Rectangle(0, c1, 25, 279, 126, 318)
        self.lcd.Draw_Rectangle(0, c1, 24, 278, 127, 319)
        self.lcd.Draw_Rectangle(0, c2, 145, 279, 246, 318)
        self.lcd.Draw_Rectangle(0, c2, 144, 278, 247, 319)

    def draw_popup_bkgd_60(self):
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Window, 14, 60, 258, 330)

    def draw_printing_screen(self):
        self.lcd.Frame_AreaCopy(1, 40, 2, 92, 14, 14, 9)  # Tune
        self.lcd.Frame_AreaCopy(1, 0, 44, 96, 58, 41, 188)  # Pause
        self.lcd.Frame_AreaCopy(1, 98, 44, 152, 58, 176, 188)  # Stop

    def draw_print_progressbar(self, percent_record=None):
        if not percent_record:
            percent_record = self.pd.get_percent()
        self.lcd.ICON_Show(self.ICON, self.ICON_Bar, 15, 93)
        self.lcd.Draw_Rectangle(1, self.lcd.BarFill_Color, 16 + percent_record * 240 / 100, 93, 256, 113)
        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Percent_Color,
            self.lcd.Color_Bg_Black, 2, 117, 133, percent_record
        )
        self.lcd.Draw_String(
            False, False, self.lcd.font8x16, self.lcd.Percent_Color, self.lcd.Color_Bg_Black, 133, 133, "%"
        )

    def draw_print_progress_elapsed(self):
        elapsed = self.pd.duration()  # print timer
        self.lcd.Draw_IntValue(
            True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 2, 42, 212, elapsed / 3600
        )
        self.lcd.Draw_String(
            False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 58, 212, ":"
        )
        self.lcd.Draw_IntValue(
            True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            2, 66, 212, (elapsed % 3600) / 60
        )

    def draw_print_progress_remain(self):
        remain_time = self.pd.remain()
        if not remain_time:
            return  # time remaining is None during warmup.
        self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                               2, 176, 212, remain_time / 3600
                               )
        self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                             192, 212, ":"
                             )
        self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                               2, 200, 212, (remain_time % 3600) / 60
                               )

    def draw_print_file_menu(self):
        self.clear_title_bar()
        self.lcd.Frame_TitleCopy(1, 52, 31, 137, 41)  # "Print file"
        self.redraw_sd_list()

    def draw_prepare_menu(self):
        self.clear_main_window()
        scroll = self.MROWS - self.index_prepare
        self.lcd.Frame_TitleCopy(1, 178, 2, 229, 14)  # "Prepare"
        self.draw_back_first(self.select_prepare.now == 0)  # < Back
        if scroll + self.PREPARE_CASE_MOVE <= self.MROWS:
            self.item_prepare_move(self.PREPARE_CASE_MOVE)  # Move >
        if scroll + self.PREPARE_CASE_DISA <= self.MROWS:
            self.item_prepare_disable(self.PREPARE_CASE_DISA)  # Disable Stepper
        if scroll + self.PREPARE_CASE_HOME <= self.MROWS:
            self.item_prepare_home(self.PREPARE_CASE_HOME)  # Auto Home
        if self.pd.HAS_Z_OFFSET_ITEM:
            if scroll + self.PREPARE_CASE_ZOFF <= self.MROWS:
                self.item_prepare_offset(self.PREPARE_CASE_ZOFF)  # Edit Z-Offset / Babystep / Set Home Offset
        if self.pd.HAS_HOTEND:
            if scroll + self.PREPARE_CASE_PLA <= self.MROWS:
                self.item_prepare_pla(self.PREPARE_CASE_PLA)  # Preheat PLA
            if scroll + self.PREPARE_CASE_ABS <= self.MROWS:
                self.item_prepare_abs(self.PREPARE_CASE_ABS)  # Preheat ABS
        if self.pd.HAS_PREHEAT:
            if scroll + self.PREPARE_CASE_COOL <= self.MROWS:
                self.item_prepare_cool(self.PREPARE_CASE_COOL)  # Cooldown
        if self.select_prepare.now:
            self.draw_menu_cursor(self.select_prepare.now)

    def draw_control_menu(self):
        self.clear_main_window()
        self.draw_back_first(self.select_control.now == 0)
        self.lcd.Frame_TitleCopy(1, 128, 2, 176, 12)  # "Control"
        self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX, self.m_base(self.CONTROL_CASE_TEMP))  # Temperature >
        self.lcd.Frame_AreaCopy(1, 84, 89, 128, 99, self.LBLX, self.m_base(self.CONTROL_CASE_MOVE))  # Motion >
        self.lcd.Frame_AreaCopy(1, 0, 104, 25, 115, self.LBLX, self.m_base(self.CONTROL_CASE_INFO))  # Info >

        if self.select_control.now and self.select_control.now < self.MROWS:
            self.draw_menu_cursor(self.select_control.now)

        # # Draw icons and lines
        self.draw_menu_line(1, self.ICON_Temperature)
        self.draw_more_icon(1)
        self.draw_menu_line(2, self.ICON_Motion)
        self.draw_more_icon(2)
        self.draw_menu_line(3, self.ICON_Info)
        self.draw_more_icon(3)

    def draw_info_menu(self):
        self.clear_main_window()

        self.lcd.Draw_String(
            False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            (self.lcd.DWIN_WIDTH - len(self.pd.MACHINE_SIZE) * self.MENU_CHR_W) / 2, 122,
            self.pd.MACHINE_SIZE
        )
        self.lcd.Draw_String(
            False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            (self.lcd.DWIN_WIDTH - len(self.pd.SHORT_BUILD_VERSION) * self.MENU_CHR_W) / 2, 195,
            self.pd.SHORT_BUILD_VERSION
        )
        self.lcd.Frame_TitleCopy(1, 190, 16, 215, 26)  # "Info"
        self.lcd.Frame_AreaCopy(1, 120, 150, 146, 161, 124, 102)
        self.lcd.Frame_AreaCopy(1, 146, 151, 254, 161, 82, 175)
        self.lcd.Frame_AreaCopy(1, 0, 165, 94, 175, 89, 248)
        self.lcd.Draw_String(
            False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            (self.lcd.DWIN_WIDTH - len(self.pd.CORP_WEBSITE_E) * self.MENU_CHR_W) / 2, 268,
            self.pd.CORP_WEBSITE_E
        )
        self.draw_back_first()
        for i in range(3):
            self.lcd.ICON_Show(self.ICON, self.ICON_PrintSize + i, 26, 99 + i * 73)
            self.lcd.Draw_Line(self.lcd.Line_Color, 16, self.m_base(2) + i * 73, 256, 156 + i * 73)

    def draw_tune_menu(self):
        self.clear_main_window()
        self.lcd.Frame_AreaCopy(1, 94, 2, 126, 12, 14, 9)
        self.lcd.Frame_AreaCopy(1, 1, 179, 92, 190, self.LBLX, self.m_base(self.TUNE_CASE_SPEED))  # Print speed
        if self.pd.HAS_HOTEND:
            self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX, self.m_base(self.TUNE_CASE_TEMP))  # Hotend...
            self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 44, self.m_base(self.TUNE_CASE_TEMP))  # Temperature
        if self.pd.HAS_HEATED_BED:
            self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX, self.m_base(self.TUNE_CASE_BED))  # Bed...
            # ...Temperature
            self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 27, self.m_base(self.TUNE_CASE_BED))
        if self.pd.HAS_FAN:
            self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX, self.m_base(self.TUNE_CASE_FAN))  # Fan speed
        if self.pd.HAS_Z_OFFSET_ITEM:
            self.lcd.Frame_AreaCopy(1, 93, 179, 141, 189, self.LBLX, self.m_base(self.TUNE_CASE_ZOFF))  # Z-offset
        self.draw_back_first(self.select_tune.now == 0)
        if self.select_tune.now:
            self.draw_menu_cursor(self.select_tune.now)

        self.draw_menu_line(self.TUNE_CASE_SPEED, self.ICON_Speed)
        self.lcd.Draw_IntValue(
            True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
            3, 216, self.m_base(self.TUNE_CASE_SPEED), self.pd.feed_rate_percentage)

        if self.pd.HAS_HOTEND:
            self.draw_menu_line(self.TUNE_CASE_TEMP, self.ICON_HotendTemp)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(self.TUNE_CASE_TEMP),
                self.pd.thermal_manager['temp_hotend'][0]['target']
            )

        if self.pd.HAS_HEATED_BED:
            self.draw_menu_line(self.TUNE_CASE_BED, self.ICON_BedTemp)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(self.TUNE_CASE_BED), self.pd.thermal_manager['temp_bed']['target'])

        if self.pd.HAS_FAN:
            self.draw_menu_line(self.TUNE_CASE_FAN, self.ICON_FanSpeed)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(self.TUNE_CASE_FAN),
                self.pd.thermal_manager['fan_speed'][0]
            )
        if self.pd.HAS_Z_OFFSET_ITEM:
            self.draw_menu_line(self.TUNE_CASE_ZOFF, self.ICON_Zoffset)
            self.lcd.Draw_Signed_Float(
                self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202,
                self.m_base(self.TUNE_CASE_ZOFF), self.pd.BABY_Z_VAR * 100
            )

    def draw_temperature_menu(self):
        self.clear_main_window()
        self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "Temperature"
        if self.pd.HAS_HOTEND:
            self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX, self.m_base(self.TEMP_CASE_TEMP))  # Nozzle...
            self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101,
                                    self.LBLX + 44, self.m_base(self.TEMP_CASE_TEMP))  # ...Temperature
        if self.pd.HAS_HEATED_BED:
            self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX, self.m_base(self.TEMP_CASE_BED))  # Bed...
            # ...Temperature
            self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 27, self.m_base(self.TEMP_CASE_BED))
        if self.pd.HAS_FAN:
            self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX, self.m_base(self.TEMP_CASE_FAN))  # Fan speed
        if self.pd.HAS_HOTEND:
            self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.m_base(self.TEMP_CASE_PLA))  # Preheat...
            self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX + 52, self.m_base(self.TEMP_CASE_PLA))  # ...PLA
            self.lcd.Frame_AreaCopy(1, 131, 119, 182, 132, self.LBLX + 79,
                                    self.m_base(self.TEMP_CASE_PLA))  # PLA setting
            self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.m_base(self.TEMP_CASE_ABS))  # Preheat...
            self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 52, self.m_base(self.TEMP_CASE_ABS))  # ...ABS
            self.lcd.Frame_AreaCopy(1, 131, 119, 182, 132, self.LBLX + 81,
                                    self.m_base(self.TEMP_CASE_ABS))  # ABS setting

        self.draw_back_first(self.select_temp.now == 0)
        if self.select_temp.now:
            self.draw_menu_cursor(self.select_temp.now)

        # Draw icons and lines
        i = 0
        if self.pd.HAS_HOTEND:
            i += 1
            self.draw_menu_line(self.ICON_SetEndTemp + self.TEMP_CASE_TEMP - 1)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(i),
                self.pd.thermal_manager['temp_hotend'][0]['target']
            )
        if self.pd.HAS_HEATED_BED:
            i += 1
            self.draw_menu_line(self.ICON_SetEndTemp + self.TEMP_CASE_BED - 1)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(i),
                self.pd.thermal_manager['temp_bed']['target']
            )
        if self.pd.HAS_FAN:
            i += 1
            self.draw_menu_line(self.ICON_SetEndTemp + self.TEMP_CASE_FAN - 1)
            self.lcd.Draw_IntValue(
                True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
                3, 216, self.m_base(i),
                self.pd.thermal_manager['fan_speed'][0]
            )
        if self.pd.HAS_HOTEND:
            # PLA/ABS items have submenus
            i += 1
            self.draw_menu_line(self.ICON_SetEndTemp + self.TEMP_CASE_PLA - 1)
            self.draw_more_icon(i)
            i += 1
            self.draw_menu_line(self.ICON_SetEndTemp + self.TEMP_CASE_ABS - 1)
            self.draw_more_icon(i)

    def draw_motion_menu(self):
        self.clear_main_window()
        self.lcd.Frame_TitleCopy(1, 144, 16, 189, 26)  # "Motion"
        self.draw_max_en(self.m_base(self.MOTION_CASE_RATE))
        self.draw_speed_en(27, self.m_base(self.MOTION_CASE_RATE))  # "Max Speed"
        self.draw_max_accel_en(self.m_base(self.MOTION_CASE_ACCEL))  # "Max Acceleration"
        self.draw_steps_per_mm(self.m_base(self.MOTION_CASE_STEPS))  # "Steps-per-mm"

        self.draw_back_first(self.select_motion.now == 0)
        if self.select_motion.now:
            self.draw_menu_cursor(self.select_motion.now)

        i = 1
        self.draw_menu_line(self.ICON_MaxSpeed + self.MOTION_CASE_RATE - 1)
        self.draw_more_icon(i)
        i += 1
        self.draw_menu_line(self.ICON_MaxSpeed + self.MOTION_CASE_ACCEL - 1)
        self.draw_more_icon(i)
        i += 1
        self.draw_menu_line(self.ICON_MaxSpeed + self.MOTION_CASE_STEPS - 1)
        self.draw_more_icon(i)

    def draw_move_menu(self):
        self.clear_main_window()
        self.lcd.Frame_TitleCopy(1, 231, 2, 265, 12)  # "Move"
        self.draw_move_en(self.m_base(1))
        self.say_x(36, self.m_base(1))  # "Move X"
        self.draw_move_en(self.m_base(2))
        self.say_y(36, self.m_base(2))  # "Move Y"
        self.draw_move_en(self.m_base(3))
        self.say_z(36, self.m_base(3))  # "Move Z"
        if self.pd.HAS_HOTEND:
            self.lcd.Frame_AreaCopy(1, 123, 192, 176, 202, self.LBLX, self.m_base(4))  # "Extruder"

        self.draw_back_first(self.select_axis.now == 0)
        if self.select_axis.now:
            self.draw_menu_cursor(self.select_axis.now)

        # Draw separators and icons
        for i in range(4):
            self.draw_menu_line(i + 1, self.ICON_MoveX + i)

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def goto_main_menu(self):
        self.check_key = self.MainMenu
        self.clear_main_window()

        self.lcd.Frame_AreaCopy(1, 0, 2, 39, 12, 14, 9)
        self.lcd.ICON_Show(self.ICON, self.ICON_LOGO, 71, 52)

        self.icon_print()
        self.icon_prepare()
        self.icon_control()
        if self.pd.HAS_ONE_STEP_LEVELING:
            self.icon_leveling(self.select_page.now == 3)
        else:
            self.icon_start_info(self.select_page.now == 3)

    def goto_print_process(self):
        self.check_key = self.PrintProcess
        self.clear_main_window()
        self.draw_printing_screen()

        self.icon_tune()
        if self.pd.printing_is_paused():
            self.icon_continue()
        else:
            self.icon_pause()
        self.icon_stop()

        # Copy into filebuf string before entry
        name = self.pd.file_name
        if name:
            npos = max(0, self.lcd.DWIN_WIDTH - len(name) * self.MENU_CHR_W) / 2
            self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White,
                                 self.lcd.Color_Bg_Black, npos, 60, name)

        self.lcd.ICON_Show(self.ICON, self.ICON_PrintTime, 17, 193)
        self.lcd.ICON_Show(self.ICON, self.ICON_RemainTime, 150, 191)

        self.draw_print_progressbar()
        self.draw_print_progress_elapsed()
        self.draw_print_progress_remain()

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def clear_title_bar(self):
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Blue, 0, 0, self.lcd.DWIN_WIDTH, 30)

    def clear_menu_area(self):
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, self.STATUS_Y)

    def clear_main_window(self):
        self.clear_title_bar()
        self.clear_menu_area()

    def clear_popup_area(self):
        self.clear_title_bar()
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, self.lcd.DWIN_HEIGHT)

    def popup_window_pause_or_stop(self):
        self.clear_main_window()
        self.draw_popup_bkgd_60()
        if self.select_print.now == 1:
            self.lcd.Draw_String(
                False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
                (272 - 8 * 11) / 2, 150,
                self.MSG_PAUSE_PRINT
            )
        elif self.select_print.now == 2:
            self.lcd.Draw_String(
                False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
                (272 - 8 * 10) / 2, 150,
                self.MSG_STOP_PRINT
            )
        self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 26, 280)
        self.lcd.ICON_Show(self.ICON, self.ICON_Cancel_E, 146, 280)
        self.draw_select_highlight(True)

    def popup_window_home(self, parking=False):
        self.clear_main_window()
        self.draw_popup_bkgd_60()
        self.lcd.ICON_Show(self.ICON, self.ICON_BLTouch, 101, 105)
        if parking:
            self.lcd.Draw_String(
                False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
                (272 - 8 * 7) / 2, 230, "Parking")
        else:
            self.lcd.Draw_String(
                False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
                (272 - 8 * 10) / 2, 230, "Homing XYZ")

        self.lcd.Draw_String(
            False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
            (272 - 8 * 23) / 2, 260, "Please wait until done.")

    def popup_window_e_temp_too_low(self):
        self.clear_main_window()
        self.draw_popup_bkgd_60()
        self.lcd.ICON_Show(self.ICON, self.ICON_TempTooLow, 102, 105)
        self.lcd.Draw_String(
            False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color,
            self.lcd.Color_Bg_Window, 20, 235,
            "Nozzle is too cold"
        )
        self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 86, 280)

    def erase_menu_cursor(self, line):
        self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, self.m_base(line) - 18, 14, self.m_base(line + 1) - 20)

    def erase_menu_text(self, line):
        self.lcd.Draw_Rectangle(
            1, self.lcd.Color_Bg_Black, self.LBLX, self.m_base(line) - 14, 271, self.m_base(line) + 28
        )

    def move_highlight(self, ffrom, newline):
        self.erase_menu_cursor(newline - ffrom)
        self.draw_menu_cursor(newline)

    def add_menu_line(self):
        self.move_highlight(1, self.MROWS)
        self.lcd.Draw_Line(
            self.lcd.Line_Color, 16, self.m_base(self.MROWS + 1) - 20, 256, self.m_base(self.MROWS + 1) - 19
        )

    def scroll_menu(self, directory):
        self.lcd.Frame_AreaMove(1, directory, self.MLINE, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, 349)
        if dir == self.DWIN_SCROLL_DOWN:
            self.move_highlight(-1, 0)
        elif dir == self.DWIN_SCROLL_UP:
            self.add_menu_line()

    # Redraw the first set of SD Files
    def redraw_sd_list(self):
        self.select_file.reset()
        self.index_file = self.MROWS
        self.clear_menu_area()  # Leave title bar unchanged
        self.draw_back_first()
        fl = self.pd.get_files()
        ed = len(fl)
        if ed > 0:
            if ed > self.MROWS:
                ed = self.MROWS
            for i in range(ed):
                self.draw_sd_item(i, i + 1)
        else:
            self.lcd.Draw_Rectangle(
                1, self.lcd.Color_Bg_Red, 10, self.m_base(3) - 10, self.lcd.DWIN_WIDTH - 10, self.m_base(4)
            )
            self.lcd.Draw_String(False, False, self.lcd.font16x32, self.lcd.Color_Yellow, self.lcd.Color_Bg_Red, (
                        self.lcd.DWIN_WIDTH - 8 * 16) / 2, self.m_base(3), "No Media")

    def completed_homing(self):
        self.pd.HMI_flag.home_flag = False
        if self.check_key == self.Last_Prepare:
            self.check_key = self.Prepare
            self.select_prepare.now = self.PREPARE_CASE_HOME
            self.index_prepare = self.MROWS
            self.draw_prepare_menu()
        elif self.check_key == self.Back_Main:
            self.pd.HMI_ValueStruct.print_speed = self.pd.feed_rate_percentage = 100
            # dwin_zoffset = TERN0(HAS_BED_PROBE, probe.offset.z)
            # planner.finish_and_disable()
            self.goto_main_menu()

    def say_x(self, inset, line):
        self.lcd.Frame_AreaCopy(1, 95, 104, 102, 114, self.LBLX + inset, line)  # "X"

    def say_y(self, inset, line):
        self.lcd.Frame_AreaCopy(1, 104, 104, 110, 114, self.LBLX + inset, line)  # "Y"

    def say_z(self, inset, line):
        self.lcd.Frame_AreaCopy(1, 112, 104, 120, 114, self.LBLX + inset, line)  # "Z"

    def say_e(self, inset, line):
        self.lcd.Frame_AreaCopy(1, 237, 119, 244, 129, self.LBLX + inset, line)  # "E"

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def icon_print(self):
        if self.select_page.now == 0:
            self.lcd.ICON_Show(self.ICON, self.ICON_Print_1, 17, 130)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 17, 130, 126, 229)
            self.lcd.Frame_AreaCopy(1, 1, 451, 31, 463, 57, 201)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Print_0, 17, 130)
            self.lcd.Frame_AreaCopy(1, 1, 423, 31, 435, 57, 201)

    def icon_prepare(self):
        if self.select_page.now == 1:
            self.lcd.ICON_Show(self.ICON, self.ICON_Prepare_1, 145, 130)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 130, 254, 229)
            self.lcd.Frame_AreaCopy(1, 33, 451, 82, 466, 175, 201)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Prepare_0, 145, 130)
            self.lcd.Frame_AreaCopy(1, 33, 423, 82, 438, 175, 201)

    def icon_control(self):
        if self.select_page.now == 2:
            self.lcd.ICON_Show(self.ICON, self.ICON_Control_1, 17, 246)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 17, 246, 126, 345)
            self.lcd.Frame_AreaCopy(1, 85, 451, 132, 463, 48, 318)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Control_0, 17, 246)
            self.lcd.Frame_AreaCopy(1, 85, 423, 132, 434, 48, 318)

    def icon_leveling(self, show):
        if show:
            self.lcd.ICON_Show(self.ICON, self.ICON_Leveling_1, 145, 246)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 246, 254, 345)
            self.lcd.Frame_AreaCopy(1, 84, 437, 120, 449, 182, 318)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Leveling_0, 145, 246)
            self.lcd.Frame_AreaCopy(1, 84, 465, 120, 478, 182, 318)

    def icon_start_info(self, show):
        if show:
            self.lcd.ICON_Show(self.ICON, self.ICON_Info_1, 145, 246)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 246, 254, 345)
            self.lcd.Frame_AreaCopy(1, 132, 451, 159, 466, 186, 318)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Info_0, 145, 246)
            self.lcd.Frame_AreaCopy(1, 132, 423, 159, 435, 186, 318)

    def icon_tune(self):
        if self.select_print.now == 0:
            self.lcd.ICON_Show(self.ICON, self.ICON_Setup_1, 8, 252)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 8, 252, 87, 351)
            self.lcd.Frame_AreaCopy(1, 0, 466, 34, 476, 31, 325)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Setup_0, 8, 252)
            self.lcd.Frame_AreaCopy(1, 0, 438, 32, 448, 31, 325)

    def icon_continue(self):
        if self.select_print.now == 1:
            self.lcd.ICON_Show(self.ICON, self.ICON_Continue_1, 96, 252)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 96, 252, 175, 351)
            self.lcd.Frame_AreaCopy(1, 1, 452, 32, 464, 121, 325)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Continue_0, 96, 252)
            self.lcd.Frame_AreaCopy(1, 1, 424, 31, 434, 121, 325)

    def icon_pause(self):
        if self.select_print.now == 1:
            self.lcd.ICON_Show(self.ICON, self.ICON_Pause_1, 96, 252)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 96, 252, 175, 351)
            self.lcd.Frame_AreaCopy(1, 177, 451, 216, 462, 116, 325)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Pause_0, 96, 252)
            self.lcd.Frame_AreaCopy(1, 177, 423, 215, 433, 116, 325)

    def icon_stop(self):
        if self.select_print.now == 2:
            self.lcd.ICON_Show(self.ICON, self.ICON_Stop_1, 184, 252)
            self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 184, 252, 263, 351)
            self.lcd.Frame_AreaCopy(1, 218, 452, 249, 466, 209, 325)
        else:
            self.lcd.ICON_Show(self.ICON, self.ICON_Stop_0, 184, 252)
            self.lcd.Frame_AreaCopy(1, 218, 423, 247, 436, 209, 325)

    def item_prepare_move(self, row):
        self.draw_move_en(self.m_base(row))  # "Move >"
        self.draw_menu_line(row, self.ICON_Axis)
        self.draw_more_icon(row)

    def item_prepare_disable(self, row):
        self.lcd.Frame_AreaCopy(1, 103, 59, 200, 74, self.LBLX, self.m_base(row))  # Disable Stepper"
        self.draw_menu_line(row, self.ICON_CloseMotor)

    def item_prepare_home(self, row):
        self.lcd.Frame_AreaCopy(1, 202, 61, 271, 71, self.LBLX, self.m_base(row))  # Auto Home"
        self.draw_menu_line(row, self.ICON_Homing)

    def item_prepare_offset(self, row):
        if self.pd.HAS_BED_PROBE:
            self.lcd.Frame_AreaCopy(1, 93, 179, 141, 189, self.LBLX, self.m_base(row))  # "Z-Offset"
            self.lcd.Draw_Signed_Float(
                self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202, self.m_base(row),
                self.pd.BABY_Z_VAR * 100
            )
        else:
            self.lcd.Frame_AreaCopy(1, 1, 76, 106, 86, self.LBLX, self.m_base(row))  # "..."
        self.draw_menu_line(row, self.ICON_SetHome)

    def item_prepare_pla(self, row):
        self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.m_base(row))  # Preheat"
        self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX + 52, self.m_base(row))  # PLA"
        self.draw_menu_line(row, self.ICON_PLAPreheat)

    def item_prepare_abs(self, row):
        self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.m_base(row))  # "Preheat"
        self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 52, self.m_base(row))  # "ABS"
        self.draw_menu_line(row, self.ICON_ABSPreheat)

    def item_prepare_cool(self, row):
        self.lcd.Frame_AreaCopy(1, 200, 76, 264, 86, self.LBLX, self.m_base(row))  # "Cooldown"
        self.draw_menu_line(row, self.ICON_Cool)

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def each_moment_update(self):
        # variable update
        update = self.pd.update_variable()
        if self.last_status != self.pd.status:
            self.last_status = self.pd.status
            print(self.pd.status)
            if self.pd.status == 'printing':
                self.goto_print_process()
            elif self.pd.status in ['operational', 'complete', 'standby', 'cancelled']:
                self.goto_main_menu()

        if self.check_key == self.PrintProcess:
            if self.pd.HMI_flag.print_finish and not self.pd.HMI_flag.done_confirm_flag:
                self.pd.HMI_flag.print_finish = False
                self.pd.HMI_flag.done_confirm_flag = True
                # show percent bar and value
                self.draw_print_progressbar(0)
                # show print done confirm
                self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 250, self.lcd.DWIN_WIDTH - 1, self.STATUS_Y)
                self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 86, 283)
            elif self.pd.HMI_flag.pause_flag != self.pd.printing_is_paused():
                # print status update
                self.pd.HMI_flag.pause_flag = self.pd.printing_is_paused()
                if self.pd.HMI_flag.pause_flag:
                    self.icon_continue()
                else:
                    self.icon_pause()
            self.draw_print_progressbar()
            self.draw_print_progress_elapsed()
            self.draw_print_progress_remain()

        if self.pd.HMI_flag.home_flag:
            if self.pd.is_homed():
                self.completed_homing()

        if update:
            self.draw_status_area(update)
        self.lcd.UpdateLCD()

    def encoder_has_data(self, val):
        if self.check_key == self.MainMenu:
            self.hmi_main_menu()
        elif self.check_key == self.SelectFile:
            self.hmi_select_file()
        elif self.check_key == self.Prepare:
            self.hmi_prepare()
        elif self.check_key == self.Control:
            self.hmi_control()
        elif self.check_key == self.PrintProcess:
            self.hmi_printing()
        elif self.check_key == self.Print_window:
            self.hmi_pause_or_stop()
        elif self.check_key == self.AxisMove:
            self.hmi_axis_move()
        elif self.check_key == self.TemperatureID:
            self.hmi_temperature()
        elif self.check_key == self.Motion:
            self.hmi_motion()
        elif self.check_key == self.Info:
            self.hmi_info()
        elif self.check_key == self.Tune:
            self.hmi_tune()
        elif self.check_key == self.PLAPreheat:
            self.hmi_pla_preheat_setting()
        elif self.check_key == self.ABSPreheat:
            self.hmi_abs_preheat_setting()
        elif self.check_key == self.MaxSpeed:
            self.hmi_max_speed()
        elif self.check_key == self.MaxAcceleration:
            self.hmi_max_acceleration()
        elif self.check_key == self.MaxJerk:
            self.hmi_max_jerk()
        elif self.check_key == self.Step:
            self.hmi_step()
        elif self.check_key == self.Move_X:
            self.hmi_move_x()
        elif self.check_key == self.Move_Y:
            self.hmi_move_y()
        elif self.check_key == self.Move_Z:
            self.hmi_move_z()
        elif self.check_key == self.Extruder:
            self.hmi_move_e()
        elif self.check_key == self.ETemp:
            self.hmi_e_temp()
        elif self.check_key == self.Homeoffset:
            self.hmi_z_offset()
        elif self.check_key == self.BedTemp:
            self.hmi_bed_temp()
        # elif self.checkkey == self.FanSpeed:
        # 	self.HMI_FanSpeed()
        elif self.check_key == self.PrintSpeed:
            self.hmi_print_speed()
        elif self.check_key == self.MaxSpeed_value:
            self.hmi_max_feed_speed_xyze()
        elif self.check_key == self.MaxAcceleration_value:
            self.hmi_max_acceleration_xyze()
        elif self.check_key == self.MaxJerk_value:
            self.hmi_max_jerk_xyze()
        elif self.check_key == self.Step_value:
            self.hmi_step_xyze()

    def get_encoder_state(self):
        if self.EncoderRateLimit:
            if self.EncodeMS > current_milli_time():
                return self.ENCODER_DIFF_NO
            self.EncodeMS = current_milli_time() + self.ENCODER_WAIT

        if self.encoder.value < self.EncodeLast:
            self.EncodeLast = self.encoder.value
            return self.ENCODER_DIFF_CW
        elif self.encoder.value > self.EncodeLast:
            self.EncodeLast = self.encoder.value
            return self.ENCODER_DIFF_CCW
        elif not GPIO.input(self.button_pin):
            if self.EncodeEnter > current_milli_time():  # prevent double clicks
                return self.ENCODER_DIFF_NO
            self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
            return self.ENCODER_DIFF_ENTER
        else:
            return self.ENCODER_DIFF_NO

    def hmi_audio_feedback(self, success=True):
        if success:
            self.pd.buzzer.tone(100, 659)
            self.pd.buzzer.tone(10, 0)
            self.pd.buzzer.tone(100, 698)
        else:
            self.pd.buzzer.tone(40, 440)
