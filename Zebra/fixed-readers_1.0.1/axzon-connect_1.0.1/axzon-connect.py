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
import sys
if sys.platform == 'linux':
    import syslog
import Opus

class RfidOperation(Enum):
    NONE            = 0
    FIND_OPUS_TAGS  = 1
    SET_STANDBY     = 2
    WRITE_CONFIG    = 3
    ARM             = 4
    SET_BAP_MODE    = 5
    READ_LOG        = 6

#Globals Constants
FIND_OPUS_TAGS_OP_PERIOD = 4.0 #Execute FIND_OPUS_TAGS at least every 4 seconds
REPORT_PASSIVE_MEASUREMENTS_PERIOD = 15.0 # seconds
SLEEP_WHEN_NOTHING_TO_DO_PERIOD = 0.5 # seconds
FORGET_TAGS_AFTER = 20.0 # seconds from the last time it was read
HIGH_POWER = 29
MID_POWER = 27
LOW_POWER = 26
POWER = HIGH_POWER
DEVELOPMENT_VERSION = False

#CONFIG_FROM_JSON_FILE_PATH = 'OpusConfig.json'
#CONFIG_FROM_JSON_FILE_PATH = 'c:\\dev\\OpusCloud\\OpusConnect\\OpusConnect\\OpusConfig.json'
CONFIG_FROM_JSON_FILE_PATH = '/apps/OpusConfig.json'

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
    global time_mark
    time_mark = datetime.now()

def time_diff(do_print = False):
     delta = datetime.now() - time_mark
     d = delta.seconds + delta.microseconds/1000000.0
     if do_print and DEVELOPMENT_VERSION:
         print("Time: " + str(d))
     return d

def ushort_array_to_hex_string(ushort_array):
    ua = ushort_array[:]
    ua.byteswap()
    b=bytes(ua)
    return b.hex()

def hex_string_to_ushort_array(hex):
    ba = bytearray.fromhex(hex)
    a= array.array("H", ba)
    a.byteswap()
    return a

def is_string_hex(stringInHex):
    try:
        n = int(stringInHex, 16)
        return True
    except:
        return False

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
        if not (type(res) == str and len(res) > 0 and len(res) % 4 == 0 and is_string_hex(res)): 
            return False
    return True

def check_epc(msg_in_json):
    if not ("idHex" in msg_in_json["data"]):
        return False
    epc = msg_in_json["data"]["idHex"]
    if not (type(epc) == str and len(epc) in [4, 8, 12, 16, 20, 24, 28, 32] and is_string_hex(epc)): 
        return False
    return True

def check_msg_from_radio_is_for_find_opus_tags_op(msg_in_json):
    try:   
        if (not check_access_results(msg_in_json, 3)):
            return False
        accessResults = msg_in_json["data"]["accessResults"]
        expected_lengths = [24, 96, 32]
        for res, l in zip(accessResults, expected_lengths):
            if not (len(res) == l): 
                return False
        return check_epc(msg_in_json)
    except Exception as e:
        log_error(f"check_msg_from_radio_is_for_find_opus_tags_op() Unexpected {e=}, {type(e)=}")
        return False

def check_msg_from_radio_is_for_read_log_data_op(msg_in_json):
    try:   
        res = check_access_results(msg_in_json, 1) and check_epc(msg_in_json)
        return res
    except Exception as e:
        log_error(f"check_msg_from_radio_is_for_read_log_data_op() Unexpected {e=}, {type(e)=}")
        return False

def new_msg_callback(msg_type, msg_in):
    try:
        #zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray("M - ", 'utf-8'))
        #zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray(msg_in, 'utf-8'))
        if msg_type != pyziotc.MSG_IN_JSON:
            return
        msg_in_json = json.loads(msg_in)
        if next_op == RfidOperation.NONE:
            return
        elif next_op == RfidOperation.FIND_OPUS_TAGS:
            if check_msg_from_radio_is_for_find_opus_tags_op(msg_in_json):
                msgs_from_radio.put_nowait(msg_in_json)
        elif next_op == RfidOperation.SET_STANDBY:
            return
        elif next_op == RfidOperation.WRITE_CONFIG:
            return
        elif next_op == RfidOperation.ARM:
            return
        elif next_op == RfidOperation.READ_LOG:
            if check_msg_from_radio_is_for_read_log_data_op(msg_in_json):
                msgs_from_radio.put_nowait(msg_in_json)
    except Exception as e:
        log_error("Unhandled Callback Exception: " + f"{e}")
        if DEVELOPMENT_VERSION:
            print(f"new_msg_callback() Unexpected {e=}, {type(e)=}")
  
# RADIO CONTROL USING REST API -------------------------------------------------------------------------

def chose_power():
    global POWER
    if POWER == HIGH_POWER:
        POWER = MID_POWER
    elif POWER == MID_POWER:
        POWER = LOW_POWER
    else:
        POWER = HIGH_POWER
    return POWER

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
    
def set_iotc_mode_magnus3_all_sensors():    
    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": [10.0],
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
            "tagPopulation": 2,
            "sel": "ALL",
            "session": "S0",
            "target": "A"
          },
          "delayAfterSelects": 3,
          "accesses": [
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
          "tagMetaData": ["ANTENNA", "RSSI", "CHANNEL"]
        }
        """
    set_iotc_mode(mode_config)

def set_iotc_mode_opus_find_tags():    
    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
          """ + str(chose_power()) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "S0",
              "action": "INVA_NOTHING",
              "membank": "USER",
              "pointer": 144,
              "length": 16,
              "mask": "0BE0",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "INVA_NOTHING",
              "membank": "USER",
              "pointer": 176,
              "length": 16,
              "mask": "0BE0",
              "truncate": 0
            },
            {
              "target": "SL",
              "action": "ASSERTSL_DEASSERTSL",
              "membank": "TID",
              "pointer": 0,
              "length": 32,
              "mask": "E2C24500",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "INVA_NOTHING",
              "membank": "USER",
              "pointer": 208,
              "length": 16,
              "mask": "0BE0",
              "truncate": 0
            }
          ],
          "delayAfterSelects": 4,
          "query": {
            "tagPopulation": 30,
            "sel": "SL",
            "session": "S0",
            "target": "A"
          },
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
                "membank": "TID",
                "wordPointer": 8,
                "wordCount": 24
              }
            },
            {
              "type": "READ",
              "config": {
                "membank": "USER",
                "wordPointer": 0,
                "wordCount": 8
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
          "tagMetaData": ["ANTENNA", "RSSI", "CHANNEL", "PC", "XPC", "MAC", "HOSTNAME"]
        }
        """
    set_iotc_mode(mode_config)

def set_iotc_mode_opus_set_bap_mode(epcs):  
    selects_list = []
    for e in epcs:
        selects_list.append("""
                    {
                  "target": "S0",
                  "action": "NOTHING_INVA",
                  "membank": "USER",
                  "pointer": 192,
                  "length": 
        """ + str(len(e)*4) + """,
                  "mask":
        """ + "\"" + e + """",
                  "truncate": 0
                }
        """)
    selects_string = ", ".join(selects_list)

    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
          """ + str(chose_power()) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "S0",
              "action": "INVB_INVA",
              "membank": "TID",
              "pointer": 0,
              "length": 32,
              "mask": "E2C24500",
              "truncate": 0
            },
        """ + selects_string + """
          ],
          "delayAfterSelects": 1,
          "query": {
            "tagPopulation": 1,
            "sel": "ALL",
            "session": "S0",
            "target": "B"
          },
          "delayBetweenAntennaCycles": {
            "type": "DISABLED",
            "duration": 0
          },
          "radioStopConditions" : {
            "duration" : 0.2,
            "tagCount" : 1
          },
          "tagMetaData": []
        }
        """
    set_iotc_mode(mode_config)

def set_iotc_mode_opus_write_configuration(epcs, tid_0x08_to_0x1F):
    # Don't write UTC timestamp (0x11 and 0x12) because the logger gets armed
    tid_0x08_to_0x10 = tid_0x08_to_0x1F[:9]
    tid_0x13_to_0x1F = tid_0x08_to_0x1F[11:]
    tid_0x08_to_0x10_hex_str = ushort_array_to_hex_string(tid_0x08_to_0x10)
    tid_0x13_to_0x1F_hex_str = ushort_array_to_hex_string(tid_0x13_to_0x1F)

    selects_list = []
    for e in epcs:
        selects_list.append("""
                    {
                  "target": "S0",
                  "action": "INVB_NOTHING",
                  "membank": "EPC",
                  "pointer": 32,
                  "length": 
        """ + str(len(e)*4) + """,
                  "mask":
        """ + "\"" + e + """",
                  "truncate": 0
                }
        """)
    selects_string = ", ".join(selects_list)

    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
        """ + str(chose_power()) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "SL",
              "action": "ASSERTSL_DEASSERTSL",
              "membank": "TID",
              "pointer": 0,
              "length": 32,
              "mask": "E2C24500",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "INVA_INVB",
              "membank": "TID",
              "pointer": 0,
              "length": 8,
              "mask": "E2",
              "truncate": 0
            },
        """ + selects_string + """
          ],
          "delayAfterSelects": 1,
          "query": {
            "tagPopulation":
        """ + str(len(e)) + """,
            "sel": "SL",
            "session": "S0",
            "target": "B"
          },
          "accesses": [
            {
              "type": "WRITE",
              "config": {
                "membank": "TID",
                "wordPointer": 8,
                "data": 
        """ + "\"" + tid_0x08_to_0x10_hex_str + """"
            }
            },
            {
              "type": "WRITE",
              "config": {
                "membank": "TID",
                "wordPointer": 19,
                "data": 
        """ + "\"" + tid_0x13_to_0x1F_hex_str + """"
            }
            }         
          ],
          "delayBetweenAntennaCycles": {
            "type": "DISABLED",
            "duration": 0
          },
          "radioStopConditions" : {
            "duration" : 0.4,
            "tagCount" : 
        """ + str(len(e)) + """
          },
          "tagMetaData": []
        }
        """
    set_iotc_mode(mode_config)

def set_iotc_mode_opus_write_utc_timestamp(epcs):
    ts = round(datetime.now(timezone.utc).timestamp())
    ts_hex = array.array('H', [(ts & 0x7FFF0000) >> 16, ts & 0x0000FFFF])
    ts_hex_str = ushort_array_to_hex_string(ts_hex)

    selects_list = []
    for e in epcs:
        selects_list.append("""
                    {
                  "target": "S0",
                  "action": "INVB_NOTHING",
                  "membank": "EPC",
                  "pointer": 32,
                  "length": 
        """ + str(len(e)*4) + """,
                  "mask":
        """ + "\"" + e + """",
                  "truncate": 0
                }
        """)
    selects_string = ", ".join(selects_list)

    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
        """ + str(chose_power()) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "SL",
              "action": "ASSERTSL_DEASSERTSL",
              "membank": "TID",
              "pointer": 0,
              "length": 32,
              "mask": "E2C24500",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "INVA_INVB",
              "membank": "TID",
              "pointer": 0,
              "length": 8,
              "mask": "E2",
              "truncate": 0
            },
        """ + selects_string + """
          ],
          "delayAfterSelects": 1,
          "query": {
            "tagPopulation": 
        """ + str(len(e)) + """,
            "sel": "ALL",
            "session": "S0",
            "target": "B"
          },
          "accesses": [
            {
              "type": "WRITE",
              "config": {
                "membank": "TID",
                "wordPointer": 17,
                "data": 
      """ + "\"" + ts_hex_str + """"
            }
            }         
          ],
          "delayBetweenAntennaCycles": {
            "type": "DISABLED",
            "duration": 0
          },
          "radioStopConditions" : {
            "duration" : 0.2,
            "tagCount" : 
        """ + str(len(e)) + """
          },
          "tagMetaData": []
        }
        """
    set_iotc_mode(mode_config)

def set_iotc_mode_opus_read_logged_data(epc, start, count):    
    start += 160 #160 is the first log address in the USER bank
    mode_config = """
        {
          "antennas": [
            1
          ],
          "environment": "LOW_INTERFERENCE",
          "transmitPower": 
          """ + str(chose_power()) + """,
          "type": "SIMPLE",
          "selects": [
            {
              "target": "S0",
              "action": "INVB_INVA",
              "membank": "TID",
              "pointer": 0,
              "length": 32,
              "mask": "E2C24500",
              "truncate": 0
            },
            {
              "target": "S0",
              "action": "NOTHING_INVA",
              "membank": "EPC",
              "pointer": 32,
              "length": 
     """ + str(len(epc)*4) + """,
              "mask":
     """ + "\"" + epc + """",
              "truncate": 0
            }
          ],
          "delayAfterSelects": 1,
          "query": {
            "tagPopulation": 1,
            "sel": "ALL",
            "session": "S0",
            "target": "B"
          },
          "accesses": [
            {
              "type": "READ",
              "config": {
                "membank": "USER",
                "wordPointer": 
     """ + str(start) + """,
                "wordCount": 
     """ + str(count) + """
              }
            }          
          ],
          "delayBetweenAntennaCycles": {
            "type": "DISABLED",
            "duration": 0
          },
          "radioStopConditions" : {
            "duration" : 0.1,
            "tagCount" : 1
          },
          "tagMetaData": ["ANTENNA", "RSSI", "CHANNEL", "PC", "XPC"]
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

# OPUS TAG CLASS --------------------------------------------------------------------

class OpusTag:
    def __init__(self, tag_status):
        self.status = tag_status
        self.priority = None
        self.next_op = RfidOperation.NONE
        self.next_step = RfidOperation.NONE
        self.num_trials = 0
        self.do_report = False
        self.reported = False
        self.time_last_reported = None
        self.time_when_found = self.status.inventories[0].timestamp
        self.time_last_seen = self.status.inventories[0].timestamp
        self.num_read_log = 0
        self.num_to_read_log = 0
        state = self.status.inventories[0].state
        if state == Opus.State.SLEEP:
            self.next_op = RfidOperation.SET_STANDBY # TODO: Check if tag is new
            self.next_step = RfidOperation.SET_STANDBY
            self.priority = 0
        if state == Opus.State.STANDBY: # Kind of weird, should not happen frequently
            self.next_op = RfidOperation.WRITE_CONFIG # TODO: Check if tag is new
            self.next_step = RfidOperation.WRITE_CONFIG
            self.priority = 5
        if state in [Opus.State.READY, Opus.State.ARMED, Opus.State.LOGGING, Opus.State.BAP_MODE, Opus.State.FINISHED]:
            self.next_op = RfidOperation.NONE
            self.next_step = RfidOperation.NONE   
            self.do_report = True
            self.priority = 200

    def _check_if_logged_data_is_available(self, next_sample):
        self.num_to_read_log = next_sample - self.num_read_log
        if self.num_to_read_log > 128:
            self.num_to_read_log = 128
        if self.num_to_read_log > 0:
            self.priority = 200
            self.next_op = RfidOperation.READ_LOG
            self.next_step = RfidOperation.READ_LOG 
        else:
            self.next_op = RfidOperation.NONE
            self.next_step = RfidOperation.NONE 

    def add_status(self, tag_status):
        t = tag_status
        self.time_last_seen = t.inventories[0].timestamp
        state = t.inventories[0].state
        last_state = self.status.inventories[len(self.status.inventories)-1].state
        #print("TID: " + self.status.tag_id.TID + ", State: " + str(state) + ", last state: " + str(last_state))

        if state == Opus.State.SLEEP:
            if last_state == Opus.State.SLEEP:
                if self.next_step == RfidOperation.SET_STANDBY:
                    self.next_op = RfidOperation.SET_STANDBY
                    if self.num_trials <= 3:
                        self.status.add_status(t, False)
                    if self.num_trials == 10:
                        self.reported = False
                        self.do_report = True
                    self.priority += 5
            else: #Very weird case, it should not happen
                if self.next_step != RfidOperation.NONE:
                    self.status.add_status(t, False)
                    self.reported = False
                    self.do_report = True
                    self.next_op = RfidOperation.NONE # Do nothing after this condition
                    self.next_step = RfidOperation.NONE
        if state == Opus.State.STANDBY:
            if self.next_step == RfidOperation.SET_STANDBY: # One of the normal cases
                self.next_op = RfidOperation.WRITE_CONFIG # TODO: Check if tag is new
                self.next_step = RfidOperation.WRITE_CONFIG
                self.num_trials = 0
                self.priority = 5
                self.status.add_status(t, False)
            elif self.next_step == RfidOperation.WRITE_CONFIG:
                if (t.inventories[0].tid_0x08_0x1F[:9] == config_from_json_file.config.tid_0x08_to_0x1F[:9]) and (t.inventories[0].tid_0x08_0x1F[11:] == config_from_json_file.config.tid_0x08_to_0x1F[11:]):
                    self.next_op = RfidOperation.ARM
                    self.next_step = RfidOperation.ARM
                    self.num_trials = 0
                    self.priority = 10
                    self.status.add_status(t, False)
                else:
                    self.next_op = RfidOperation.WRITE_CONFIG # TODO: Check if tag is new
                    self.next_step = RfidOperation.WRITE_CONFIG
                    if self.num_trials <= 3:
                        self.status.add_status(t, False)
                    if self.num_trials == 10:
                        self.reported = False
                        self.do_report = True
                    self.priority += 5
            elif self.next_step == RfidOperation.ARM:
                self.next_op = RfidOperation.ARM
                if self.num_trials <= 3:
                    self.status.add_status(t, False)
                if self.num_trials == 10:
                    self.reported = False
                    self.do_report = True
                self.priority += 5

        if state in [Opus.State.READY, Opus.State.ARMED, Opus.State.LOGGING, Opus.State.BAP_MODE, Opus.State.FINISHED]:
            if self.next_step == RfidOperation.ARM:
                self.priority = 400
                self.status.add_status(t, False)
                self.reported = False
                self.do_report = True
                self.next_op = RfidOperation.NONE
                self.next_step = RfidOperation.NONE 
            else:
                self.status.add_status(t, True)
                self._check_if_logged_data_is_available(t.inventories[0].next_sample) 

                # Check to see if it's time to report passive measurements
                time_now = datetime.now(timezone.utc) 
                if self.time_last_reported == None:
                    self.time_last_reported = time_now
                delta = time_now - self.time_last_reported
                d = delta.seconds + delta.microseconds/1000000.0
                if d > REPORT_PASSIVE_MEASUREMENTS_PERIOD: 
                    self.reported = False
                    self.do_report = True

    def add_logged_data(self, data_in_json):
        hex_string = data_in_json["data"]["accessResults"][0]
        hex_array = hex_string_to_ushort_array(hex_string)      
        self.status.logged_data.arm_time = self.status.inventories[0].arm_time
        self.status.logged_data.log_delay = self.status.logger_config.num_delayed_start_periods
        self.status.logged_data.log_period_in_seconds = self.status.logger_config.log_interval.period_in_seconds()
        self.status.logged_data.first_sample_number = self.num_read_log
        self.status.logged_data.data = hex_array
        self.num_read_log += len(hex_array)
        self.reported = False
        self.do_report = True
        self._check_if_logged_data_is_available(self.status.inventories[0].next_sample) 

# CONFIG FROM JSON FILE -------------------------------------------------------------

class ConfigFromJsonFile:
    def __init__(self):
        self.valid = False
        self.error_msg = ""
        self.path = CONFIG_FROM_JSON_FILE_PATH
        self.j_config = None
        self.config = None 

    def load_config(self):
        try:
            with open(self.path, 'r') as file:
                self.j_config = json.load(file)
            self.valid = True
        except:
            self.error_msg = "Error while loading OpusConfig.json file"
            self.valid = False
        try:
            if self.valid:
                self.config = Opus.Configuration(self.j_config)
                self.valid = self.config.valid
                self.error_msg = self.config.error_msg
        except:
            self.error_msg = "Error while creating Configuration from OpusConfig.json file"
            self.valid = False

# MAIN ALGORITHMS -------------------------------------------------------------------

def get_data_from_radio(max_time_in_sec):
    try:
        return msgs_from_radio.get(True, max_time_in_sec)
    except:
        return None
    
#returns [next_operation, list of tags]
def determine_next_opus_operation():
    delta = datetime.now(timezone.utc) - last_execution_of_get_opus_tags
    d = delta.seconds + delta.microseconds/1000000.0
    if d > FIND_OPUS_TAGS_OP_PERIOD: 
        #print("QQQQQQQQQQQQQQQQQQQQQQ")
        return [RfidOperation.FIND_OPUS_TAGS, []]  

    highest_priority = 10000000000
    num_trials = 10000000000
    tag = None
    for value in opus_tags.values():
        if value.next_op != RfidOperation.NONE:
            if value.priority < highest_priority or (value.priority == highest_priority and value.num_trials < num_trials):
                highest_priority = value.priority
                num_trials = value.num_trials
                tag = value
    if tag == None:
        time.sleep(SLEEP_WHEN_NOTHING_TO_DO_PERIOD) 
        next_operation = RfidOperation.FIND_OPUS_TAGS
    else:
        next_operation = tag.next_op
    
    if (next_operation in [RfidOperation.SET_STANDBY, RfidOperation.WRITE_CONFIG, RfidOperation.ARM]) or (next_operation in [RfidOperation.FIND_OPUS_TAGS] and tag != None):
        tags = [tag]
        count = 1
        for value in opus_tags.values():
            if value.status.tag_id.TID != tag.status.tag_id.TID and value.next_op == next_operation:
                tags.append(value)
                count += 1
                if count >= 30: #TODO: Fine tune 30
                    break
    else:
        tags = [] if tag == None else [tag]
    return [next_operation, tags]
    
def execute_opus_operation(tags):
    global last_execution_of_get_opus_tags
    epcs = []
    for t in tags:
        t.priority += 20
        t.num_trials += 1
        epcs.append(t.status.tag_id.EPC)
    if next_op in [RfidOperation.SET_STANDBY, RfidOperation.WRITE_CONFIG, RfidOperation.ARM]:
        for t in tags:
            t.next_op = RfidOperation.FIND_OPUS_TAGS
    if next_op == RfidOperation.FIND_OPUS_TAGS:
        last_execution_of_get_opus_tags = datetime.now(timezone.utc)
        set_iotc_mode_opus_find_tags()
    elif next_op == RfidOperation.SET_STANDBY:
        set_iotc_mode_opus_set_bap_mode(epcs)
    elif next_op == RfidOperation.WRITE_CONFIG:
        c = config_from_json_file.config
        set_iotc_mode_opus_write_configuration(epcs, c.tid_0x08_to_0x1F)
    elif next_op == RfidOperation.ARM:
        set_iotc_mode_opus_write_utc_timestamp(epcs)
    elif next_op == RfidOperation.READ_LOG:
        tag = tags[0]
        set_iotc_mode_opus_read_logged_data(tag.status.tag_id.EPC, tag.num_read_log, tag.num_to_read_log)
    start_iotc_radio()

def receive_data(tags):
    mark_time()
    processed_tags = []
    if next_op == RfidOperation.FIND_OPUS_TAGS:
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
                if TID not in processed_tags:   
                    s = Opus.StatusZebraIOTC(msg)
                    if s.valid == False:
                        if DEVELOPMENT_VERSION:
                            print(s.error_msg)
                        continue
                    processed_tags.append(TID)
                    #print("TID: " + TID)
                    if TID not in opus_tags:           
                        opus_tags[TID] = OpusTag(s)
                    else:
                        opus_tags[TID].add_status(s)
    elif next_op == RfidOperation.READ_LOG:
        tag = tags[0]
        while True:
            t = time_diff()
            if t > 0.45:
                break
            msg = get_data_from_radio(0.05)
            if msg != None:
                expected_EPC = tag.status.tag_id.EPC
                expected_TID = tag.status.tag_id.TID
                EPC = msg["data"]["idHex"].upper()
                if EPC == expected_EPC:
                    opus_tags[expected_TID].add_logged_data(msg)
                    break
    else: # for operations where response doesn't matter
        time.sleep(0.1) #TODO: Review

def report_tag(value):
    d = value.status.to_dict()
    msg_in_json = json.dumps(d)
    zio.send_next_msg(pyziotc.MSG_OUT_DATA, bytearray(msg_in_json, 'utf-8'))
    value.time_last_reported = datetime.now(timezone.utc) 
    value.do_report = False
    value.reported = True
    value.status.logged_data.data = array.array('H', [])

def report_results():
    for value in opus_tags.values():
        if value.do_report:
            report_tag(value)

def delete_old_tags():
    tags_to_remove = []
    time_now = datetime.now(timezone.utc)
    for key, value in opus_tags.items():
        delta = time_now - value.time_last_seen
        d = delta.seconds + delta.microseconds/1000000.0
        if d > FORGET_TAGS_AFTER:
            if value.reported == False:
                report_tag(value)
            tags_to_remove.append(key)
    for tag in tags_to_remove:
        opus_tags[tag] = None
        del opus_tags[tag]

def get_terminal_input():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None

def print_next_op(tags):
    epcs = []
    vfcs = []
    for t in tags:
        EPC = t.status.tag_id.EPC
        if len(EPC) >= 4: 
            epcs.append(EPC[len(EPC)-4:])
        else:
            epcs.append(EPC)
        VFC = str(t.status.inventories[0].on_chip_rssi)
        vfcs.append(VFC)
    epcs_string = ", ".join(epcs)
    vfcs_string = ", ".join(vfcs) 

    print("Nex Op: " + next_op.name + " EPCS: " + epcs_string + " VFCS: " + vfcs_string)  

# MAIN ---------------------------------------------------------------------
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
            last_execution_of_get_opus_tags = datetime.now(timezone.utc)
            opus_tags = dict() # {string TID, class OpusTag}
            next_op = RfidOperation.NONE
            time_mark = None         
        except:
            log_error("Unable to Initialize Program")
            msgs_from_radio = None
            zio = None
            iotc_rest = None
            last_execution_of_get_opus_tags = None
            opus_tags = None
            time.sleep(30.0)
        else:
            log_info("Program Initialized")
            break
    
    # Verify Opus configuration file is correct 
    while True:
        config_from_json_file = ConfigFromJsonFile()
        config_from_json_file.load_config()
        if config_from_json_file.valid:
            break
        else:
            log_error(config_from_json_file.error_msg)
            time.sleep(20.0)

    # Working loop
    turn_on_led("GREEN")
    loop_number = 1
    terminate_program = False
    num_continuous_exceptions = 0
    while True:  
        try:
            if DEVELOPMENT_VERSION:
                print("\nLoop: " + str(loop_number) + ", Queue Length:" + str(msgs_from_radio.qsize()) + ", Dic:" + str(len(opus_tags)))
                loop_number += 1 
            op = determine_next_opus_operation()
            next_op = op[0]
            tags = op[1]
            if DEVELOPMENT_VERSION:
                print_next_op(tags)
            #print('A')
            execute_opus_operation(tags)
            #print('B')
            receive_data(tags)
            #print('C')
            report_results()
            #print('D')
            delete_old_tags()
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
