#
#  /* Copyright (c) 2025 RFMicron, Inc. dba Axzon Inc.
#  *
#  * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  * THE SOFTWARE.
#  */

# TODOs

import pyziotc
import json
import time
import http.client
from http.client import HTTPConnection
import queue
from enum import Enum
import collections.abc
from datetime import datetime, timezone, timedelta
import array
import select
import copy
import sys
if sys.platform == 'linux':
    import syslog
import Magnus
import RfidUtility

#Globals Constants
MIN_RF_POWER = 10
MAX_RF_POWER = 29
MIN_ON_CHIP_RSSI_FOR_TEMPERATURE = 6
MAX_ON_CHIP_RSSI_FOR_TEMPERATURE = 18
REPORT_PASSIVE_MEASUREMENTS_PERIOD = 10.0 # seconds
FORGET_TAGS_AFTER = 15.0 # seconds
DEVELOPMENT_VERSION = False

#Global Variables
g_time_mark = None
g_rf_power_mod = None

# UTILS ----------------------------------------------------------------------------------------------------

def turn_on_led(color):
    try:
        if color not in {"GREEN", "AMBER", "RED"}:
            return
        led_msg = bytearray(json.dumps({"type":"LED","color":color,"led":3}), "utf-8")		
        zio.send_next_msg(pyziotc.MSG_OUT_GPO, led_msg)
    except:
        pass

def mark_time():
    global g_time_mark
    g_time_mark = datetime.now()

def time_diff(do_print = False):
     delta = datetime.now() - g_time_mark
     d = delta.seconds + delta.microseconds/1000000.0
     if do_print and DEVELOPMENT_VERSION:
         print("Time: " + str(d))
     return d

def log_error(msg):
    try:
        if sys.platform == 'linux':
            syslog.syslog(syslog.LOG_ERR, "ERROR: " + msg)
        if DEVELOPMENT_VERSION:
            print(msg)
    except:
        pass

def log_info(msg):
    try:
        if sys.platform == 'linux':
            syslog.syslog(syslog.LOG_ERR, "INFO: " + msg) #syslog.LOG_INFO doesn't work for the FX9600
        if DEVELOPMENT_VERSION:
            print(msg)
    except:
        pass

# RADIO CALLBACK ---------------------------------------------------------------------------------------

def check_access_results(msg_in_json, num_res):
    if not (type(msg_in_json) == dict and "data" in msg_in_json):
        return False
    if not (type(msg_in_json["data"]) == dict and "accessResults" in msg_in_json["data"]):
        return False
    accessResults = msg_in_json["data"]["accessResults"]
    if not(type(accessResults) == list and len(accessResults) == num_res):
        return False
    for res in accessResults:
        if not (type(res) == str and len(res) > 0 and len(res) % 4 == 0 and RfidUtility.is_string_hex(res)): 
            return False
    return True

def check_epc(msg_in_json):
    if not ("idHex" in msg_in_json["data"]):
        return False
    epc = msg_in_json["data"]["idHex"]
    if not (type(epc) == str and len(epc) in [4, 8, 12, 16, 20, 24, 28, 32] and RfidUtility.is_string_hex(epc)): 
        return False
    return True

def check_msg_from_radio_is_for_find_magnus_tags_op(msg_in_json):
    try:   
        if (not check_access_results(msg_in_json, 3)):
            return False
        accessResults = msg_in_json["data"]["accessResults"]
        expected_lengths = [24, 16, 12]
        for res, l in zip(accessResults, expected_lengths):
            if not (len(res) == l): 
                return False
        return check_epc(msg_in_json)
    except Exception as e:
        log_error(f"check_msg_from_radio_is_for_find_magnus_tags_op() Unexpected {e=}, {type(e)=}")
        return False

def new_msg_callback(msg_type, msg_in):
    try:
        #zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray("M - ", 'utf-8'))
        #zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray(msg_in, 'utf-8'))
        if msg_type != pyziotc.MSG_IN_JSON:
            return
        msg_in_json = json.loads(msg_in)
        if check_msg_from_radio_is_for_find_magnus_tags_op(msg_in_json):
            msgs_from_radio.put_nowait(msg_in_json)

    except Exception as e:
        log_error("Unhandled Callback Exception: " + f"{e}")
        if DEVELOPMENT_VERSION:
            print(f"new_msg_callback() Unexpected {e=}, {type(e)=}")
  
# RADIO CONTROL USING REST API -------------------------------------------------------------------------

def set_iotc_mode(mode_in_json):
    iotc_rest.request('PUT', '/cloud/mode', mode_in_json)
    res = iotc_rest.getresponse()
    if res.status != 200 or res.reason != "OK":
        if DEVELOPMENT_VERSION:
            print(res.status, res.reason)	
    res.read()    
    
def get_iotc_mode():
    iotc_rest.request('GET', '/cloud/mode', "")
    res = iotc_rest.getresponse()
    if res.status != 200 or res.reason != "OK":
        if DEVELOPMENT_VERSION:
            print(res.status, res.reason)
    data = res.read()
    if DEVELOPMENT_VERSION:
        print(data)    
    
def set_iotc_mode_magnus3_all_sensors(rf_power_level):    
    #print("Power: " + str(rf_power_level))
    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
          """ + str(rf_power_level) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "S0",
              "action": "INVA_INVB",
              "membank": "USER",
              "pointer": 208,
              "length": 8,
              "mask": "1F",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "INVA_INVB",
              "membank": "USER",
              "pointer": 224,
              "length": 0,
              "mask": "",
              "truncate": 0
            }
          ],
          "query": {
            "tagPopulation": 12,
            "sel": "ALL",
            "session": "S0",
            "target": "A"
          },
          "delayAfterSelects": 3,
          "accesses": [
            {
              "type": "READ",
              "config": {
                "membank": "TID",
                "wordPointer": 0,
                "wordCount": 6
              }
            },
            {
              "type": "READ",
              "config": {
                "membank": "USER",
                "wordPointer": 8,
                "wordCount": 4
              }
            },
            {
              "type": "READ",
              "config": {
                "membank": "RESERVED",
                "wordPointer": 12,
                "wordCount": 3
              }
            }
          ],
          "delayBetweenAntennaCycles": {
            "type": "DISABLED",
            "duration": 0
          },
          "radioStopConditions" : {
            "duration" : 0.4
          },
          "tagMetaData": ["ANTENNA", "RSSI", "CHANNEL", "MAC", "HOSTNAME"]
        }
        """
    set_iotc_mode(mode_config)

def stop_iotc_radio():
    iotc_rest.request('PUT','/cloud/stop', '')
    res = iotc_rest.getresponse()
    if res.status != 200 or res.reason != "OK":
        if DEVELOPMENT_VERSION:
            print(res.status, res.reason)	
    res.read()  

def start_iotc_radio():
    #stop_iotc_radio()
    msgs_from_radio.queue.clear()    
    iotc_rest.request('PUT','/cloud/start', '')
    res = iotc_rest.getresponse()
    if res.status != 200 or res.reason != "OK":
       if DEVELOPMENT_VERSION:
           print(res.status, res.reason)
    res.read()  
    #iotc_rest.close()
    pass

# MAGNUS TAG CLASSES -----------------------------------------------------------------

class TemperatureMeas:
    def __init__(self, calibration, time_stamp, temperature_code, on_chip_rssi, rssi, antenna, power):
        self.valid = False
        self.requested_power = None # Otherwise measurement is not good
        self.desired_power = None # To improve the measurement. Move to center of rssi range
        if temperature_code < 1200 or temperature_code > 3400:  # can not be real
            return
        
        min_diff = on_chip_rssi - MIN_ON_CHIP_RSSI_FOR_TEMPERATURE
        if min_diff < 0:
            self.requested_power = power + 2
            if min_diff < -3:
                self.requested_power = power + 3
            if self.requested_power > MAX_RF_POWER:
                self.requested_power = MAX_RF_POWER
            return
        max_diff = MAX_ON_CHIP_RSSI_FOR_TEMPERATURE - on_chip_rssi
        if max_diff < 0:
            self.requested_power = power - 2
            if max_diff < -3:
                self.requested_power = power - 3
            if max_diff < -6:
                self.requested_power = power - 4
            if max_diff < -9:
                self.requested_power = power - 5
            if self.requested_power < MIN_RF_POWER:
                self.requested_power = MIN_RF_POWER
            return

        self.valid = True
        
        if min_diff < 2:
            self.desired_power = power + 1  
            if self.desired_power > MAX_RF_POWER:
                self.desired_power = MAX_RF_POWER
        if max_diff < 2:
            self.desired_power = power - 1        
            if self.desired_power < MIN_RF_POWER:
                self.desired_power = MIN_RF_POWER  
                
        self.temp_in_c = calibration.get_temperature_in_c(temperature_code)
        self.time_stamp = time_stamp  
        self.rssi = rssi 
        self.on_chip_rssi = on_chip_rssi
        self.antenna = antenna
            
class SensorCodeMeas:
    def __init__(self):
        valid = False

class MagnusTag:
    def __init__(self, jdata, power):
        self.valid = False
        self.time_when_found = None
        self.time_last_reported = None
        self.time_last_seen = None
        self.on_chip_rssis = []
        self.rssis = []
        self.antennas = []
        self.sensor_code_meas = []
        self.temperature_meas = []
        self.requested_powers = []
        self.desired_powers= []
        temp_cal_words = RfidUtility.hex_string_to_ushort_array(jdata["data"]["accessResults"][1])
        self.temp_cal_data = Magnus.TemperatureCalibration(temp_cal_words)
        self.valid = self.temp_cal_data.valid
        if self.valid == False:
            return
        self.TID = jdata["data"]["accessResults"][0].upper()
        self.EPC = jdata["data"]["idHex"].upper()
        self.reader_host = jdata["data"]["hostName"]
        self.reader_mac = jdata["data"]["MAC"] 
        self.decode_measurements(jdata, power)
        self.time_when_found = self.time_last_seen

    def add_reading(self, jdata, power):
        self.decode_measurements(jdata, power)
        pass

    def decode_measurements(self, jdata, power):
        ts = jdata["timestamp"]
        self.time_last_seen = datetime.fromisoformat(ts[:len(ts)-2]+':'+ts[len(ts)-2:]) #translate to ISO UTC    
        if len(self.rssis) >= 100:
            self.rssis.pop(0)
            self.on_chip_rssis.pop(0)
        rssi = round(jdata["data"]["peakRssi"], 1)
        self.rssis.append(rssi)
        channel = round(jdata["data"]["channel"] * 1000, 0)
        antenna = jdata["data"]["antenna"]
        if antenna not in self.antennas:
            self.antennas.append(antenna)
        sensor_words = RfidUtility.hex_string_to_ushort_array(jdata["data"]["accessResults"][2])
        sensor_code = sensor_words[0]
        on_chip_rssi = sensor_words[1]
        temperature_code = sensor_words[2]
        self.on_chip_rssis.append(on_chip_rssi)
        temperature = TemperatureMeas(self.temp_cal_data, self.time_last_seen, temperature_code, on_chip_rssi, rssi, antenna, power)
        if temperature.valid:
            if len(self.temperature_meas) >= 20:
                self.temperature_meas.pop(0)
            self.temperature_meas.append(temperature)
        if temperature.requested_power is not None:
            if len(self.requested_powers) >= 20:
                self.requested_powers.pop(0)
            self.requested_powers.append(temperature.requested_power)        
        if temperature.desired_power is not None:
            if len(self.desired_powers) >= 20:
                self.desired_powers.pop(0)
            self.desired_powers.append(temperature.desired_power)   

    def get_report_in_dict(self):
        d = dict()
        d["version"] = "1.0.0"
        d["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")   # "2024-12-25T12:07:44.345000Z"
        d["TID"] = self.TID
        d["EPC"] = self.EPC
        d["readerHost"] = self.reader_host      # "FX9600F10AE0"
        d["readerMAC"] = self.reader_mac        # "84:24:8D:EE:2A:E8"
        d["antennas"] = self.antennas
        num_readings = len(self.rssis)
        d["numReadings"] = num_readings
        average = 0;
        if num_readings > 0:
            for val in self.rssis:
                average += val
            average /= num_readings
            d["avgRssi"] = average
        else:
            d["avgRssi"] = None
        average = 0;
        if num_readings > 0:
            for val in self.on_chip_rssis:
                average += val
            average /= num_readings
            d["avgOnChipRssi"] = average
        else:
            d["avgOnChipRssi"] = None
        
        d_temp = dict()
        d_temp["celsius"] = None
        d_temp["fahrenheit"] = None
        d_temp["avgOnChipRssi"] = None
        d_temp["avgRssi"] = None
        d_temp["numReadings"] = 0
        d_temp["antennas"] = []
        num_readings = len(self.temperature_meas)
        if num_readings >= 3:
            avg = 0
            for t in self.temperature_meas:
                avg += t.temp_in_c
            avg /= num_readings
            valid_temps = []
            avgOnChipRssi = 0.0
            avgRssi = 0.0
            antennas = []
            for t in self.temperature_meas:
                if abs(t.temp_in_c - avg) < 3.0:
                    valid_temps.append(t.temp_in_c)
                avgOnChipRssi += t.on_chip_rssi
                avgRssi += t.rssi
                if t.antenna not in antennas:
                    antennas.append(t.antenna)
            avgOnChipRssi /= num_readings
            avgRssi /= num_readings
            num_readings = len(valid_temps)
            if num_readings >= 3:
                temp_in_c = 0
                for t in valid_temps:
                    temp_in_c += t
                temp_in_c /= num_readings
                d_temp["celsius"] = temp_in_c
                d_temp["fahrenheit"] = (9.0 * temp_in_c / 5.0) + 32.0
                d_temp["avgOnChipRssi"] = avgOnChipRssi
                d_temp["avgRssi"] = avgRssi
                d_temp["numReadings"] = num_readings
                d_temp["antennas"] = antennas
        d["temperature"] = d_temp

        d_sensor = dict()
        d_sensor["code"] = None
        d_sensor["normalizedFreq"] = None
        d_sensor["avgOnChipRssi"] = None
        d_sensor["avgRssi"] = None
        d_sensor["numReadings"] = 0
        d_sensor["antennas"] = []
        d["sensorCode"] = d_sensor

        return d

    def clear(self):
        self.on_chip_rssis = []
        self.rssis = []
        self.antennas = []
        self.sensor_code_meas = []
        self.temperature_meas = []

    def get_requested_power(self):
        requested_power = 0
        num = 0
        for pwr in self.requested_powers:
           requested_power += pwr
           num += 1
        if num == 0:
            return None
        else:
            return round(requested_power / num)

    def get_desired_power(self):
        desired_power = 0
        num = 0
        for pwr in self.desired_powers:
           desired_power += pwr
           num += 1
        if num == 0:
            return None
        else:
            return round(desired_power / num)

# RF POWER MODULATION ---------------------------------------------------------------

class PowerModulation:
    default_powers = [MIN_RF_POWER, 15, 20, 25, MAX_RF_POWER]
    
    def __init__(self):
        self.current_power = PowerModulation.default_powers[0]
        self.power_idx = 0
        self.requested = []
        self.req_accepted = []

    def get_next_power(self):
        if self.power_idx < len(PowerModulation.default_powers):
            self.current_power = PowerModulation.default_powers[self.power_idx]
            self.power_idx += 1
            if self.power_idx == len(PowerModulation.default_powers):
                if len(self.requested) == 0:
                    self.power_idx = 0
                else:
                    self.req_accepted = self.requested
                    self.requested = []
        else:
            if len(self.req_accepted) > 0:
                self.current_power = self.req_accepted.pop(0)
                if len(self.req_accepted) == 0:
                    self.power_idx = 0
        return self.current_power

    def get_current_power(self):
        return self.current_power
 
# MAIN ALGORITHMS -------------------------------------------------------------------

def get_data_from_radio(max_time_in_sec):
    try:
        return msgs_from_radio.get(True, max_time_in_sec)
    except:
        return None
    
def execute_magnus_operation():
    set_iotc_mode_magnus3_all_sensors(g_power_mod.get_next_power())
    start_iotc_radio()

def receive_data():
    mark_time()
    while True:
        t = time_diff()
        if t > 0.45:
            return
        if t > 0.25 and msgs_from_radio.empty():
            stop_iotc_radio()
            return
        msg = get_data_from_radio(0.1)
        if msg != None:
            TID = msg["data"]["accessResults"][0].upper()
            #TODO: verify is Magnus3
            #if DEVELOPMENT_VERSION:
            #    print("TID: " + TID)
            if TID not in magnus_tags:
                mt = MagnusTag(msg, g_power_mod.get_current_power())
                if mt.valid == False:
                    continue
                magnus_tags[TID] = mt
            else:
                magnus_tags[TID].add_reading(msg, g_power_mod.get_current_power())

def report_tag(tag):
    report = tag.get_report_in_dict()
    msg_in_json = json.dumps(report)
    zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray(msg_in_json, 'utf-8'))
    tag.time_last_reported = datetime.now(timezone.utc) 
    tag.clear()

def report_results():
    for tag in magnus_tags.values():
        time_now = datetime.now(timezone.utc)
        if tag.time_last_reported == None:
            delta = time_now - tag.time_when_found
            d = delta.seconds + delta.microseconds/1000000.0
            if d > 2.0:
                report_tag(tag)
        else:
            delta = time_now - tag.time_last_reported
            d = delta.seconds + delta.microseconds/1000000.0
            if d >= REPORT_PASSIVE_MEASUREMENTS_PERIOD:
                report_tag(tag)

def delete_old_tags():
    tags_to_remove = []
    time_now = datetime.now(timezone.utc)
    for key, value in magnus_tags.items():
        delta = time_now - value.time_last_seen
        d = delta.seconds + delta.microseconds/1000000.0
        if d > FORGET_TAGS_AFTER:
            if value.time_last_reported == None:
                report_tag(value)
            tags_to_remove.append(key)
    for tag in tags_to_remove:
        magnus_tags[tag] = None
        del magnus_tags[tag]

def adjust_rf_power():
    requested_powers = []
    for tag in magnus_tags.values():
        req = tag.get_requested_power()
        if req is not None and req not in requested_powers:
            requested_powers.append(req)

    if len(requested_powers) < 5:
        for tag in magnus_tags.values():
            req = tag.get_desired_power()
            if req is not None and req not in requested_powers and len(requested_powers) < 10:
                requested_powers.append(req)
   
    g_power_mod.requested = requested_powers
   
def get_terminal_input():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None  

# MAIN ---------------------------------------------------------------------

# Global Variables
g_power_mod = PowerModulation()

# Main Loop
do_once = True
while True:

    # Initialization loop. Keep trying until successful
    while True:
        try:
            msgs_from_radio = queue.Queue(0)
            if do_once:
                zio = pyziotc.Ziotc()
                zio.reg_new_msg_callback(new_msg_callback)
                do_once = False
            turn_on_led("RED")
            iotc_rest = HTTPConnection("127.0.0.1")
            magnus_tags = dict() # {string TID, class MagnusTag}
            g_time_mark = None         
        except:
            log_error("Unable to Initialize Program")
            msgs_from_radio = None
            zio = None
            iotc_rest = None
            magnus_tags = None
            time.sleep(30.0)
        else:
            log_info("Program Initialized")
            break
    
    # Working loop
    turn_on_led("GREEN")
    loop_number = 1
    terminate_program = False
    num_continuous_exceptions = 0
    while True:  
        try:
            if DEVELOPMENT_VERSION:
                print("\nLoop: " + str(loop_number) + ", Queue Length:" + str(msgs_from_radio.qsize()) + ", Dic:" + str(len(magnus_tags)))
                loop_number += 1 
            #print('A')
            execute_magnus_operation()
            #print('B')
            receive_data()
            #print('C')
            report_results()
            #print('D')
            delete_old_tags()
            #print('E')
            adjust_rf_power()
            time.sleep(0.1) # 'Give' time to the radio to do stuff TODO: Check if it's really needed
            if DEVELOPMENT_VERSION:
                terminal_input = get_terminal_input()
                if terminal_input != None:
                    terminate_program = True
                    break
            num_continuous_exceptions = 0
        except Exception as e:
            turn_on_led("RED")
            log_error("Unhandled Exception: " + f"{e}")
            time.sleep(0.2)
            num_continuous_exceptions += 1
            if num_continuous_exceptions > 10:
                time.sleep(2.0)
                zio = None
                break
            turn_on_led("GREEN")

    if terminate_program:
        break

if terminate_program:
    turn_on_led("AMBER")
    log_info("Program terminated by the user using terminal keyboard")
else: # In theory this case should not happen
    turn_on_led("RED")
    log_error("Unexpected program termination")
    
log_info("Program finished execution")
