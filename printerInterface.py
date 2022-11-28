import threading
import errno
import select
import socket
import json
import requests
from requests.exceptions import ConnectionError
import atexit
import time
import asyncio
import logging


class NozzlePosition:
    x = 0.0
    y = 0.0
    z = 0.0
    e = 0.0
    home_x = False
    home_y = False
    home_z = False

    def homing(self):
        self.home_x = False
        self.home_y = False
        self.home_z = False


class AxisEnum:
    X_AXIS = 0
    A_AXIS = 0
    Y_AXIS = 1
    B_AXIS = 1
    Z_AXIS = 2
    C_AXIS = 2
    E_AXIS = 3
    X_HEAD = 4
    Y_HEAD = 5
    Z_HEAD = 6
    E0_AXIS = 3
    E1_AXIS = 4
    E2_AXIS = 5
    E3_AXIS = 6
    E4_AXIS = 7
    E5_AXIS = 8
    E6_AXIS = 9
    E7_AXIS = 10
    ALL_AXES = 0xFE
    NO_AXIS = 0xFF


class HMIValueT:
    E_Temp = 0
    Bed_Temp = 0
    Fan_speed = 0
    print_speed = 100
    Max_Feedspeed = 0.0
    Max_Acceleration = 0.0
    Max_Jerk = 0.0
    Max_Step = 0.0
    Move_X_scale = 0.0
    Move_Y_scale = 0.0
    Move_Z_scale = 0.0
    Move_E_scale = 0.0
    offset_value = 0.0
    show_mode = 0  # -1: Temperature control    0: Printing temperature


class HMIFlagT:
    language = 0
    pause_flag = False
    pause_action = False
    print_finish = False
    done_confirm_flag = False
    select_flag = False
    home_flag = False
    heat_flag = False  # 0: heating done  1: during heating
    ETempTooLow_flag = False
    leveling_offset_flag = False
    feedspeed_axis = AxisEnum()
    acc_axis = AxisEnum()
    jerk_axis = AxisEnum()
    step_axis = AxisEnum()


class Buzzer:
    def tone(self, t, n):
        pass


class MaterialPreset:
    def __init__(self, name, hotend_temp, bed_temp, fan_speed=100):
        self.name = name
        self.hotend_temp = hotend_temp
        self.bed_temp = bed_temp
        self.fan_speed = fan_speed


class KlippySocket:
    def __init__(self, uds_filename, callback=None):
        self.webhook_socket = self.webhook_socket_create(uds_filename)
        self.lock = threading.Lock()
        self.poll = select.poll()
        self.stop_threads = False
        self.poll.register(self.webhook_socket, select.POLLIN | select.POLLHUP)
        self.socket_data = ""
        self.t = threading.Thread(target=self.polling)
        self.callback = callback
        self.lines = []
        self.t.start()
        atexit.register(self.klippy_exit)

    def klippy_exit(self):
        print("Shutting down Klippy Socket")
        self.stop_threads = True
        self.t.join()

    @staticmethod
    def webhook_socket_create(uds_filename):
        webhook_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        webhook_socket.setblocking(False)
        print("Waiting for connect to %s\n" % (uds_filename,))
        while 1:
            try:
                webhook_socket.connect(uds_filename)
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    time.sleep(0.1)
                    continue
                print(
                    "Unable to connect socket %s [%d,%s]\n" % (
                        uds_filename, e.errno,
                        errno.errorcode[e.errno]
                    ))
                exit(-1)
            break
        print("Connection.\n")
        return webhook_socket

    def process_socket(self):
        data = self.webhook_socket.recv(4096).decode()
        if not data:
            print("Socket closed\n")
            exit(0)
        parts = data.split('\x03')
        parts[0] = self.socket_data + parts[0]
        self.socket_data = parts.pop()
        for line in parts:
            if self.callback:
                self.callback(line)

    def queue_line(self, line):
        with self.lock:
            self.lines.append(line)

    def send_line(self):
        if len(self.lines) == 0:
            return
        line = self.lines.pop(0).strip()
        if not line or line.startswith('#'):
            return
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            print("ERROR: Unable to parse line\n")
            return
        cm = json.dumps(m, separators=(',', ':'))
        wdm = '{}\x03'.format(cm)
        self.webhook_socket.send(wdm.encode())

    def polling(self):
        while True:
            if self.stop_threads:
                break
            res = self.poll.poll(1000.)
            for _ in res:
                self.process_socket()
            with self.lock:
                self.send_line()


class MoonrakerSocket:
    def __init__(self, address, port, api_key):
        self.s = requests.Session()
        self.s.headers.update({
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        })
        self.base_address = 'http://' + address + ':' + str(port)


class PrinterData:
    event_loop = None
    HAS_HOTEND = True
    HOTENDS = 1
    HAS_HEATED_BED = True
    HAS_FAN = False
    HAS_Z_OFFSET_ITEM = True
    HAS_ONE_STEP_LEVELING = False
    HAS_PREHEAT = True
    HAS_BED_PROBE = False
    PREVENT_COLD_EXTRUSION = True
    EXTRUDE_MIN_TEMP = 170
    EXTRUDE_MAXLENGTH = 200

    HEATER_0_MAXTEMP = 275
    HEATER_0_MINTEMP = 5
    HOTEND_OVERSHOOT = 15

    MAX_E_TEMP = HEATER_0_MAXTEMP - HOTEND_OVERSHOOT
    MIN_E_TEMP = HEATER_0_MINTEMP

    BED_OVERSHOOT = 10
    BED_MAX_TEMP = 150
    BED_MIN_TEMP = 5

    BED_MAX_TARGET = BED_MAX_TEMP - BED_OVERSHOOT
    MIN_BED_TEMP = BED_MIN_TEMP

    X_MIN_POS = 0.0
    Y_MIN_POS = 0.0
    Z_MIN_POS = 0.0
    Z_MAX_POS = 200

    Z_PROBE_OFFSET_RANGE_MIN = -20
    Z_PROBE_OFFSET_RANGE_MAX = 20

    buzzer = Buzzer()

    BABY_Z_VAR = 0
    feed_rate_percentage = 100
    temp_hot = 0
    temp_bed = 0

    HMI_ValueStruct = HMIValueT()
    HMI_flag = HMIFlagT()

    current_position = NozzlePosition()

    thermal_manager = {
        'temp_bed': {'celsius': 20, 'target': 120},
        'temp_hotend': [{'celsius': 20, 'target': 120}],
        'fan_speed': [100]
    }

    material_preset = [
        MaterialPreset('PLA', 200, 60),
        MaterialPreset('ABS', 210, 100)
    ]
    files = None
    MACHINE_SIZE = "220x220x250"
    SHORT_BUILD_VERSION = "1.00"
    CORP_WEBSITE_E = "https://www.klipper3d.org/"

    def __init__(self, api_key, url='127.0.0.1'):
        self.X_MAX_POS = 0
        self.Y_MAX_POS = 0
        self.file_name = ""
        self.job_info = None
        self.status = None
        self.absolute_extrude = None
        self.absolute_moves = None
        self.op = MoonrakerSocket(url, 80, api_key)
        self.ks = KlippySocket('/tmp/klippy_uds', callback=self.klippy_callback)
        subscribe = {
            "id": 4001,
            "method": "objects/subscribe",
            "params": {
                "objects": {
                    "toolhead": [
                        "position"
                    ]
                },
                "response_template": {}
            }
        }
        self.klippy_z_offset = \
            '{"id": 4002, "method": "objects/query", "params": {"objects": {"configfile": ["config"]}}}'
        self.klippy_home = \
            '{"id": 4003, "method": "objects/query", "params": {"objects": {"toolhead": ["homed_axes"]}}}'

        self.ks.queue_line(json.dumps(subscribe))
        self.ks.queue_line(self.klippy_z_offset)
        self.ks.queue_line(self.klippy_home)

        self.event_loop = asyncio.new_event_loop()
        threading.Thread(target=self.event_loop.run_forever, daemon=True).start()

    def klippy_callback(self, line):
        klippy_data = json.loads(line)
        status = None
        if 'result' in klippy_data:
            if 'status' in klippy_data['result']:
                status = klippy_data['result']['status']
        if 'params' in klippy_data:
            if 'status' in klippy_data['params']:
                status = klippy_data['params']['status']

        if status:
            if 'toolhead' in status:
                if 'position' in status['toolhead']:
                    self.current_position.x = status['toolhead']['position'][0]
                    self.current_position.y = status['toolhead']['position'][1]
                    self.current_position.z = status['toolhead']['position'][2]
                    self.current_position.e = status['toolhead']['position'][3]
                if 'homed_axes' in status['toolhead']:
                    if 'x' in status['toolhead']['homed_axes']:
                        self.current_position.home_x = True
                    if 'y' in status['toolhead']['homed_axes']:
                        self.current_position.home_y = True
                    if 'z' in status['toolhead']['homed_axes']:
                        self.current_position.home_z = True

            if 'configfile' in status:
                if 'config' in status['configfile']:
                    if 'bltouch' in status['configfile']['config']:
                        if 'z_offset' in status['configfile']['config']['bltouch']:
                            if status['configfile']['config']['bltouch']['z_offset']:
                                self.BABY_Z_VAR = float(status['configfile']['config']['bltouch']['z_offset'])

            # print(status)

    def is_homed(self):
        if self.current_position.home_x and self.current_position.home_y and self.current_position.home_z:
            return True
        else:
            self.ks.queue_line(self.klippy_home)
            return False

    def offset_z(self, new_offset):
        # print('new z offset:', new_offset)
        self.BABY_Z_VAR = new_offset
        self.send_g_code('ACCEPT')

    def add_mm(self, axs, new_offset):
        gc = 'TESTZ Z={}'.format(new_offset)
        print(axs, gc)
        self.send_g_code(gc)

    def probe_calibrate(self):
        self.send_g_code('G28')
        self.send_g_code('PROBE_CALIBRATE')
        self.send_g_code('G1 Z0')

    # ------------- OctoPrint Function ----------

    def get_rest(self, path):
        r = self.op.s.get(self.op.base_address + path)
        d = r.content.decode('utf-8')
        try:
            return json.loads(d)
        except json.JSONDecodeError:
            print('Decoding JSON has failed')
        return None

    def _post_rest(self, path, data):
        self.op.s.post(self.op.base_address + path, json=data)

    def post_rest(self, path, data):
        self.event_loop.call_soon_threadsafe(asyncio.create_task, self._post_rest(path, data))

    def init_webservices(self):
        try:
            requests.get(self.op.base_address)
        except ConnectionError:
            print('Web site does not exist')
            return
        else:
            print('Web site exists')
        if self.get_rest('/api/printer') is None:
            return
        self.update_variable()
        # alternative approach
        # full_version = self.getREST('/printer/info')['result']['software_version']
        # self.SHORT_BUILD_VERSION = '-'.join(full_version.split('-',2)[:2])
        self.SHORT_BUILD_VERSION = self.get_rest(
            '/machine/update/status?refresh=false'
        )['result']['version_info']['klipper']['version']

        data = self.get_rest('/printer/objects/query?toolhead')['result']['status']
        toolhead = data['toolhead']
        volume = toolhead['axis_maximum']  # [x,y,z,w]
        self.MACHINE_SIZE = "{}x{}x{}".format(
            int(volume[0]),
            int(volume[1]),
            int(volume[2])
        )
        self.X_MAX_POS = int(volume[0])
        self.Y_MAX_POS = int(volume[1])

    def get_files(self, refresh=False):
        if not self.files or refresh:
            self.files = self.get_rest('/server/files/list')["result"]
        names = []
        for fl in self.files:
            names.append(fl["path"])
        return names

    def update_variable(self):
        query = '/printer/objects/query?extruder&heater_bed&gcode_move&fan'
        data = self.get_rest(query)['result']['status']
        gcm = data['gcode_move']
        z_offset = gcm['homing_origin'][2]  # z offset
        # flow_rate = gcm['extrude_factor'] * 100  # flow rate percent
        self.absolute_moves = gcm['absolute_coordinates']  # absolute or relative
        self.absolute_extrude = gcm['absolute_extrude']  # absolute or relative
        # speed = gcm['speed']  # current speed in mm/s
        # print_speed = gcm['speed_factor'] * 100  # print speed percent
        bed = data['heater_bed']  # temperature, target
        extruder = data['extruder']  # temperature, target
        fan = data['fan']
        update = False
        try:
            if self.thermal_manager['temp_bed']['celsius'] != int(bed['temperature']):
                self.thermal_manager['temp_bed']['celsius'] = int(bed['temperature'])
                update = True
            if self.thermal_manager['temp_bed']['target'] != int(bed['target']):
                self.thermal_manager['temp_bed']['target'] = int(bed['target'])
                update = True
            if self.thermal_manager['temp_hotend'][0]['celsius'] != int(extruder['temperature']):
                self.thermal_manager['temp_hotend'][0]['celsius'] = int(extruder['temperature'])
                update = True
            if self.thermal_manager['temp_hotend'][0]['target'] != int(extruder['target']):
                self.thermal_manager['temp_hotend'][0]['target'] = int(extruder['target'])
                update = True
            if self.thermal_manager['fan_speed'][0] != int(fan['speed'] * 100):
                self.thermal_manager['fan_speed'][0] = int(fan['speed'] * 100)
                update = True
            if self.BABY_Z_VAR != z_offset:
                self.BABY_Z_VAR = z_offset
                self.HMI_ValueStruct.offset_value = z_offset * 100
                update = True
        except Exception as e:
            logging.error("unknown key, {}".format(e))
        self.job_info = self.get_rest('/printer/objects/query?virtual_sdcard&print_stats')['result']['status']
        if self.job_info:
            self.file_name = self.job_info['print_stats']['filename']
            self.status = self.job_info['print_stats']['state']
            self.HMI_flag.print_finish = self.get_percent() == 100.0
        return update

    def printing_is_paused(self):
        return self.job_info['print_stats']['state'] == "paused" or self.job_info['print_stats']['state'] == "pausing"

    def get_percent(self):
        if self.job_info['virtual_sdcard']['is_active']:
            return self.job_info['virtual_sdcard']['progress'] * 100
        else:
            return 0

    def duration(self):
        if self.job_info['virtual_sdcard']['is_active']:
            return self.job_info['print_stats']['print_duration']
        return 0

    def remain(self):
        percent = self.get_percent()
        duration = self.duration()
        if percent:
            total = duration / (percent / 100)
            return total - duration
        return 0

    def open_and_print_file(self, filenum):
        self.file_name = self.files[filenum]['path']
        self.post_rest('/printer/print/start', data={'filename': self.file_name})

    def cancel_job(self):  # fixed
        print('Canceling job:')
        self.post_rest('/printer/print/cancel', data=None)

    def pause_job(self):  # fixed
        print('Pausing job:')
        self.post_rest('/printer/print/pause', data=None)

    def resume_job(self):  # fixed
        print('Resuming job:')
        self.post_rest('printer/print/resume', data=None)

    def set_feed_rate(self, fr):
        self.feed_rate_percentage = fr
        self.send_g_code('M220 S%s' % fr)

    def home(self, home_z=False):  # fixed using gcode
        script = 'G28 X Y'
        if home_z:
            script += ' Z'
        self.send_g_code(script)

    def move_relative(self, axis, distance, speed):
        self.send_g_code('%s \n%s %s%s F%s%s' % ('G91', 'G1', axis, distance, speed,
                                                 '\nG90' if self.absolute_moves else ''))

    def move_absolute(self, axis, position, speed):
        self.send_g_code('%s \n%s %s%s F%s%s' % ('G90', 'G1', axis, position, speed,
                                                 '\nG91' if not self.absolute_moves else ''))

    def send_g_code(self, gcode):
        self.post_rest('/printer/gcode/script', data={'script': gcode})

    def disable_all_heaters(self):
        self.set_ext_temp(0)
        self.set_bed_temp(0)

    def zero_fan_speeds(self):
        pass

    def preheat(self, profile):
        if profile == "PLA":
            self.pre_heat(self.material_preset[0].bed_temp, self.material_preset[0].hotend_temp)
        elif profile == "ABS":
            self.pre_heat(self.material_preset[1].bed_temp, self.material_preset[1].hotend_temp)

    @staticmethod
    def save_settings():
        print('saving settings')
        return True

    def set_ext_temp(self, target, toolnum=0):
        self.send_g_code('M104 T%s S%s' % (toolnum, target))

    def set_bed_temp(self, target):
        self.send_g_code('M140 S%s' % target)

    def pre_heat(self, bedtemp, exttemp):
        self.set_bed_temp(bedtemp)
        self.set_ext_temp(exttemp)

    def set_z_offset(self, offset):
        self.send_g_code('SET_GCODE_OFFSET Z=%s MOVE=1' % offset)
