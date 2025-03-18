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

import json
from enum import Enum
from datetime import datetime, timezone, timedelta
import array
import copy

def hex_string_to_ushort_array(hex):
    ba = bytearray.fromhex(hex)
    a= array.array("H", ba)
    a.byteswap()
    return a

#---------------------- CONFIGURATION

class LogInterval:
    allowed_values = {
        ( 1,   "seconds" ) : ( True,   0x00 ),
		( 5,   "seconds" ) : ( True,   0x01 ),
		( 10,  "seconds" ) : ( True,   0x02 ),
		( 15,  "seconds" ) : ( True,   0x03 ),
		( 20,  "seconds" ) : ( True,   0x04 ),
		( 25,  "seconds" ) : ( True,   0x05 ),
		( 30,  "seconds" ) : ( True,   0x06 ),
		( 1,   "minutes" ) : ( True,   0x07 ),
		( 2,   "minutes" ) : ( True,   0x08 ),
		( 3,   "minutes" ) : ( True,   0x09 ),
		( 4,   "minutes" ) : ( True,   0x0A ),
		( 5,   "minutes" ) : ( False,  0x00 ),
		( 6,   "minutes" ) : ( True,   0x0B ),
		( 7,   "minutes" ) : ( True,   0x0C ),
		( 10,  "minutes" ) : ( False,  0x01 ),
		( 15,  "minutes" ) : ( False,  0x02 ),
		( 20,  "minutes" ) : ( False,  0x03 ),
		( 25,  "minutes" ) : ( False,  0x04 ),
		( 30,  "minutes" ) : ( False,  0x05 ),
		( 35,  "minutes" ) : ( False,  0x06 ),
		( 40,  "minutes" ) : ( False,  0x07 ),
		( 1,   "hours"   ) : ( False,  0x08 ),
		( 2,   "hours"   ) : ( False,  0x09 ),
		( 3,   "hours"   ) : ( False,  0x0A ),
		( 4,   "hours"   ) : ( False,  0x0B ),
		( 5,   "hours"   ) : ( False,  0x0C ),
		( 6,   "hours"   ) : ( False,  0x0D ),
		( 7,   "hours"   ) : ( False,  0x0E ),
        ( 8,   "hours"   ) : ( False,  0x0F ) 
        }  
    allowed_values_rev = {
        ( True,   0x00 ) : ( 1,   "seconds" ),
		( True,   0x01 ) : ( 5,   "seconds" ),
		( True,   0x02 ) : ( 10,  "seconds" ),
		( True,   0x03 ) : ( 15,  "seconds" ),
		( True,   0x04 ) : ( 20,  "seconds" ),
		( True,   0x05 ) : ( 25,  "seconds" ),
		( True,   0x06 ) : ( 30,  "seconds" ),
		( True,   0x07 ) : ( 1,   "minutes" ),
		( True,   0x08 ) : ( 2,   "minutes" ),
		( True,   0x09 ) : ( 3,   "minutes" ),
		( True,   0x0A ) : ( 4,   "minutes" ),
		( False,  0x00 ) : ( 5,   "minutes" ),
		( True,   0x0B ) : ( 6,   "minutes" ),
		( True,   0x0C ) : ( 7,   "minutes" ),
		( False,  0x01 ) : ( 10,  "minutes" ),
		( False,  0x02 ) : ( 15,  "minutes" ),
		( False,  0x03 ) : ( 20,  "minutes" ),
		( False,  0x04 ) : ( 25,  "minutes" ),
		( False,  0x05 ) : ( 30,  "minutes" ),
		( False,  0x06 ) : ( 35,  "minutes" ),
		( False,  0x07 ) : ( 40,  "minutes" ),
		( False,  0x08 ) : ( 1,   "hours"   ),
		( False,  0x09 ) : ( 2,   "hours"   ),
		( False,  0x0A ) : ( 3,   "hours"   ),
		( False,  0x0B ) : ( 4,   "hours"   ),
		( False,  0x0C ) : ( 5,   "hours"   ),
		( False,  0x0D ) : ( 6,   "hours"   ),
		( False,  0x0E ) : ( 7,   "hours"   ),
        ( False,  0x0F ) : ( 8,   "hours"   )        
        }

    def __init__(self, p1, p2):
        self.ssd_sampling_regime_override = True
        self.sampling_regime = 0x06
        self.value = 30
        self.units = "seconds"
        self.valid = False
        if isinstance(p1, int) and isinstance(p2, str):
            self.value = p1
            self.units = p2
            if (p1, p2) in self.allowed_values:
                val = self.allowed_values[(p1, p2)]
                self.ssd_sampling_regime_override = val[0]
                self.sampling_regime = val[1]
                self.valid = True
        if isinstance(p1, bool) and isinstance(p2, int):
            self.ssd_sampling_regime_override = p1
            self.sampling_regime = p2
            if (p1, p2) in self.allowed_values_rev:
                val = self.allowed_values_rev[(p1, p2)]
                self.value = val[0]
                self.units = val[1]
                self.valid = True
                
    def period_in_seconds(self):
        if self.valid == False:
            return None
        if self.units == "seconds":
            unit_in_seconds = 1
        elif self.units == "minutes":
            unit_in_seconds = 60
        else:
            unit_in_seconds = 3600
        return self.value * unit_in_seconds

class NumberOfSamplesToLog(Enum):
    S_512   = 0
    S_1024  = 1
    S_1536  = 2
    S_2048  = 3
    S_2560  = 4
    S_3072  = 5
    S_3584  = 6
    S_4096  = 7
    def num_to_enum(num):
        str_num = "S_" + str(num)
        if (str_num) in [num.name for num in NumberOfSamplesToLog]:
            return NumberOfSamplesToLog[str_num]
        else:
            return None

    def get_number(self):
        return int(self.name[2:])

class LedMode(Enum):
    CONTINUOUS = 0
    ON_DEMAND = 1
    def str_to_enum(str_enum):
        if (str_enum) in [led_mode.name for led_mode in LedMode]:
            return LedMode[str_enum]
        else:
            return None

class AntiTamperPolarity(Enum):
    DETECT_CONNECTION_OR_LIGHT = 0
    DETECT_DISCONNECTION_OR_DARKNESS = 1
    def str_to_enum(str_enum):
        if (str_enum) in [polarity.name for polarity in AntiTamperPolarity]:
            return AntiTamperPolarity[str_enum]
        else:
            return None

class Configuration:
    # It is assumed that the following config has no errors
    default_config = """
        {
            "logging": 
            {
                "interval": 
                {
                    "value": 30,
                    "units": "seconds"
                },
                "delayedStart": 
                {
                    "value": 1
                },
                "numberOfSamples": 
                {
                    "value": 4096
                }
            },
            "temperatureLimits": 
            {
                "lowerLimit": 
                {
                    "value": -5.0,
                    "alarmDelay": 
                    {
                        "value": 1
                    }
                },
                "upperLimit": 
                {
                    "value": 42.0,
                    "alarmDelay": 
                    {
                        "value": 1
                    }
                }
            },
            "led": 
            {
                "enabled": true,
                "mode": 
                {
                    "value": "ON_DEMAND"
                },
                "offTime": 
                {
                    "value": 2
                },
                "onTime": 
                {
                    "value": 50
                }
            },
            "fingerSpot": 
            {
                "enabled": true,
                "useForLoggerArming": false
            },
            "antiTamper": 
            {
                "enabled": false,
                "polarity": 
                {
                    "value": "DETECT_CONNECTION_OR_LIGHT"
                }
            }
        }
    """
    default_j_config = json.loads(default_config)

    # It can be initialized in four different ways
        # With no parameters it creates a "default" configuration
        # With one string parameter in JSON format 
        # With one dictionary parameter in JSON format
        # With one array of 24 integers corresponding to tid_0x08_to_0x1F
    def __init__(self, p_config = None):
        self.valid = False
        self.error_msg = ""
        self.tid_0x08_to_0x1F = array.array('H',[0x9100, 0x02A0, 0x0FB0, 0x0000, 0x0000, 0x0000, 0x0000, 0x0030, 0x0490, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x1E08, 0x0000, 0x07D0, 0x09C4, 0x3004, 0x0108])
        self.tid_0x20_to_0x29 = array.array('H',[0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0A00, 0x000F, 0x0200, 0x0011])
        self.j_config = None
        self.log_interval = None
        self.num_delayed_start_periods = None

        if p_config == None:
            self.j_config =  copy.deepcopy(Configuration.default_j_config)
            self.valid = self._config_json_to_int_array()
        elif isinstance(p_config, str):
            self.valid = self._config_str_to_json(p_config)
            if self.valid:
                self.valid = self._config_json_to_int_array()
        elif isinstance(p_config, dict):
            self.j_config = p_config
            self.valid = self._config_json_to_int_array()
        elif isinstance(p_config, array.array) and len(p_config) == 24:
            self.tid_0x08_to_0x1F = array.array('H', p_config)
            self.valid = self._config_int_array_to_json()  
        else:
            self.error_msg = "Unable to create Configuration object. Wrong initialization parameters"

    def _check_config_schema(self, dic1, dic2, key_path = ""):
        for k, v in dic1.items():
            k_path = key_path + "\\" + str(k)
            if k not in dic2:
                self.error_msg = "Opus config error. Missing section: " + k_path
                return False
            if type(dic1[k]) != type(dic2[k]):
                    self.error_msg = "Opus config error. Wrong value type at section: " + k_path + ", Value: " + str(dic2[k])
                    return False
            if isinstance(dic1[k], dict):
                if not self._check_config_schema(dic1[k], dic2[k], k_path):
                    return False
        return True

    def _config_json_to_int_array(self):
        if self._check_config_schema(Configuration.default_j_config, self.j_config) == False:
            return False

        #Log interval
        log_interval_value = self.j_config["logging"]["interval"]["value"]
        log_interval_units = self.j_config["logging"]["interval"]["units"]
        self.log_interval = LogInterval(log_interval_value, log_interval_units)
        if self.log_interval.valid == False:
            self.error_msg = "Opus config error. Wrong value or units in logging interval"
            return False
        if self.log_interval.ssd_sampling_regime_override:
            self.tid_0x08_to_0x1F[0] |= 0x0100
        else:
            self.tid_0x08_to_0x1F[0] &= 0xFEFF
        self.tid_0x08_to_0x1F[7] &= 0xFF87
        self.tid_0x08_to_0x1F[7] |= (self.log_interval.sampling_regime & 0x000F) << 3
        
        #Delayed logger start periods
        self.num_delayed_start_periods = self.j_config["logging"]["delayedStart"]["value"]
        if self.num_delayed_start_periods not in [0, 1, 2, 3, 4, 5, 6, 7]:
            self.error_msg = "Opus config error. Num delay start periods is out of range"
            return False
        self.tid_0x08_to_0x1F[8] &= 0xE3FF
        self.tid_0x08_to_0x1F[8] |= (self.num_delayed_start_periods & 0x0007) << 10
        
        #Number of samples to log
        num_samples_to_log = self.j_config["logging"]["numberOfSamples"]["value"]
        num_samples_enum = NumberOfSamplesToLog.num_to_enum(num_samples_to_log)
        if num_samples_enum == None:
            self.error_msg = "Opus config error. Wrong value in numberOfSamples to log"
            return False
        self.tid_0x08_to_0x1F[18] &= 0xE3FF
        self.tid_0x08_to_0x1F[18] |= (num_samples_enum.value & 0x0007) << 10

        #Temperature lower limit
        temp_lower_limit = self.j_config["temperatureLimits"]["lowerLimit"]["value"]
        if temp_lower_limit < -128.0 or temp_lower_limit > 127.9375:
            self.error_msg = "Opus config error. Lower temperature limit out of range"
            return False
        temp_lower_limit_int = int(16.0 * temp_lower_limit)
        self.tid_0x08_to_0x1F[2] &= 0xF000
        self.tid_0x08_to_0x1F[2] |= (temp_lower_limit_int & 0x0FFF)

        #Temperature lower limit alarm delay
        temp_lower_limit_alarm_delay = self.j_config["temperatureLimits"]["lowerLimit"]["alarmDelay"]["value"]
        if temp_lower_limit_alarm_delay not in [0, 1, 2, 3, 4, 5, 6, 7]:
            self.error_msg = "Opus config error. Temperature lower limit alarm delay out of range"
            return False
        self.tid_0x08_to_0x1F[8] &= 0xFF8F
        self.tid_0x08_to_0x1F[8] |= (temp_lower_limit_alarm_delay & 0x0007) << 4

        #Temperature upper limit
        temp_upper_limit = self.j_config["temperatureLimits"]["upperLimit"]["value"]
        if temp_upper_limit < -128.0 or temp_upper_limit > 127.9375:
            self.error_msg = "Opus config error. Upper temperature limit out of range"
            return False
        temp_upper_limit_int = int(16.0 * temp_upper_limit)
        self.tid_0x08_to_0x1F[1] &= 0xF000
        self.tid_0x08_to_0x1F[1] |= (temp_upper_limit_int & 0x0FFF)

        #Temperature upper limit alarm delay
        temp_upper_limit_alarm_delay = self.j_config["temperatureLimits"]["upperLimit"]["alarmDelay"]["value"]
        if temp_upper_limit_alarm_delay not in [0, 1, 2, 3, 4, 5, 6, 7]:
            self.error_msg = "Opus config error. Temperature upper limit alarm delay out of range"
            return False
        self.tid_0x08_to_0x1F[8] &= 0xFC7F
        self.tid_0x08_to_0x1F[8] |= (temp_upper_limit_alarm_delay & 0x0007) << 7

        #LED enabled
        led_enabled = self.j_config["led"]["enabled"]
        self.tid_0x08_to_0x1F[22] &= 0xDFFF
        self.tid_0x08_to_0x1F[22] |= 0x2000 if led_enabled else 0x0000

        #LED mode
        led_mode = self.j_config["led"]["mode"]["value"]
        led_mode_enum = LedMode.str_to_enum(led_mode)
        if led_mode_enum == None:
            self.error_msg = "Opus config error. Wrong LED mode"
            return False
        self.tid_0x08_to_0x1F[22] &= 0xEFFF
        self.tid_0x08_to_0x1F[22] |= 0x1000 if led_mode_enum == LedMode.ON_DEMAND else 0x0000

        #LED off time
        led_off_time = self.j_config["led"]["offTime"]["value"]
        if led_off_time < 2 or led_off_time > 64 or led_off_time % 2 != 0:
            self.error_msg = "Opus config error. LED off time is out of range"
            return False
        led_off_time = (led_off_time >> 1) - 1
        self.tid_0x08_to_0x1F[22] &= 0xFC1F
        self.tid_0x08_to_0x1F[22] |= (led_off_time & 0x001F) << 5

        #LED on time
        led_on_time = self.j_config["led"]["onTime"]["value"]
        if led_on_time < 10 or led_on_time > 320 or led_on_time % 10 != 0:
            self.error_msg = "Opus config error. LED off time is out of range"
            return False
        led_on_time = (led_on_time // 10) - 1
        self.tid_0x08_to_0x1F[22] &= 0xFFE0
        self.tid_0x08_to_0x1F[22] |= (led_on_time & 0x001F)

        #FingerSpot enabled
        finger_spot_enabled = self.j_config["fingerSpot"]["enabled"]
        self.tid_0x08_to_0x1F[0] &= 0xEFFF
        self.tid_0x08_to_0x1F[0] |= 0x1000 if finger_spot_enabled else 0x0000

        #FingerSpot for logger arming
        finger_spot_for_logger_arming = self.j_config["fingerSpot"]["useForLoggerArming"]
        self.tid_0x08_to_0x1F[0] &= 0xFFF7
        self.tid_0x08_to_0x1F[0] |= 0x0008 if finger_spot_for_logger_arming else 0x0000

        #AntiTamper enabled
        anti_tamper_enabled = self.j_config["antiTamper"]["enabled"]
        self.tid_0x08_to_0x1F[0] &= 0xFBFF
        self.tid_0x08_to_0x1F[0] |= 0x0400 if anti_tamper_enabled else 0x0000

        #AntiTamper polarity
        anti_tamper_polarity = self.j_config["antiTamper"]["polarity"]["value"]
        anti_tamper_polarity_enum = AntiTamperPolarity.str_to_enum(anti_tamper_polarity)
        if anti_tamper_polarity_enum == None:
            self.error_msg = "Opus config error. Wrong AntiTamper polarity value"
            return False
        polarity = anti_tamper_polarity_enum in [AntiTamperPolarity.DETECT_DISCONNECTION_OR_DARKNESS]
        self.tid_0x08_to_0x1F[0] &= 0xF7FF
        self.tid_0x08_to_0x1F[0] |= 0x0800 if polarity else 0x0000

        return True
    
    def _config_str_to_json(self, config_in_string):
        try:	
            self.j_config = json.loads(config_in_string)
            return True
        except Exception as err:
            error_msg = "Error while converting string configuration to JSON configuration"
            return False

    # This is the case where a config is read from a tag. It's possible that the config may be corrupted
    def _config_int_array_to_json(self):
        self.j_config = dict()

        #Log interval
        ssd_sampling_regime_override = (self.tid_0x08_to_0x1F[0] & 0x0100) == 0x0100
        sampling_regime = (self.tid_0x08_to_0x1F[7] >> 3) & 0x000F
        self.log_interval = LogInterval(ssd_sampling_regime_override, sampling_regime)
        #if self.log_interval.valid == False: # Allow to read a corrupted configuration
            #return False
        self.j_config["logging"] = dict()
        self.j_config["logging"]["interval"] = dict()
        if self.log_interval.valid:
            self.j_config["logging"]["interval"]["value"] = self.log_interval.value
            self.j_config["logging"]["interval"]["units"] = self.log_interval.units
        else: #TODO: Handle this case in a better way
            self.j_config["logging"]["interval"]["value"] = None
            self.j_config["logging"]["interval"]["units"] = "Error" 

        #Delayed logger start periods
        self.num_delayed_start_periods = (self.tid_0x08_to_0x1F[8] >> 10) & 0x0007
        self.j_config["logging"]["delayedStart"] = dict()
        self.j_config["logging"]["delayedStart"]["value"] = self.num_delayed_start_periods
        
        #Number of samples to log
        num_samples_index = (self.tid_0x08_to_0x1F[18] >> 10) & 0x0007
        num_samples_enum = NumberOfSamplesToLog(num_samples_index)
        self.j_config["logging"]["numberOfSamples"] = dict()
        self.j_config["logging"]["numberOfSamples"]["value"] = num_samples_enum.get_number()

        #Temperature lower limit
        temp_lower_limit_int = self.tid_0x08_to_0x1F[2] & 0x0FFF
        temp_lower_limit = temp_lower_limit_int << 4
        temp_lower_limit_f = round(int.from_bytes(temp_lower_limit.to_bytes(2,'big'), byteorder='big', signed=True) / 256.0, 2)
        self.j_config["temperatureLimits"] = dict()
        self.j_config["temperatureLimits"]["lowerLimit"] = dict()
        self.j_config["temperatureLimits"]["lowerLimit"]["value"] = temp_lower_limit_f

        #Temperature lower limit alarm delay
        temp_lower_limit_alarm_delay = (self.tid_0x08_to_0x1F[8] >> 4) & 0x0007
        self.j_config["temperatureLimits"]["lowerLimit"]["alarmDelay"] = dict()
        self.j_config["temperatureLimits"]["lowerLimit"]["alarmDelay"]["value"] = temp_lower_limit_alarm_delay

        #Temperature upper limit
        temp_upper_limit_int = self.tid_0x08_to_0x1F[1] & 0x0FFF
        temp_upper_limit = temp_upper_limit_int << 4
        temp_upper_limit_f = round(int.from_bytes(temp_upper_limit.to_bytes(2,'big'), byteorder='big', signed=True) / 256.0, 2)
        self.j_config["temperatureLimits"]["upperLimit"] = dict()
        self.j_config["temperatureLimits"]["upperLimit"]["value"] = temp_upper_limit_f

        #Temperature upper limit alarm delay
        temp_upper_limit_alarm_delay = (self.tid_0x08_to_0x1F[8] >> 7) & 0x0007
        self.j_config["temperatureLimits"]["upperLimit"]["alarmDelay"] = dict()
        self.j_config["temperatureLimits"]["upperLimit"]["alarmDelay"]["value"] = temp_upper_limit_alarm_delay

        #LED enabled
        led_enabled = (self.tid_0x08_to_0x1F[22] & 0x2000) == 0x2000
        self.j_config["led"] = dict()
        self.j_config["led"]["enabled"] = led_enabled

        #LED mode
        led_mode_bit_set = (self.tid_0x08_to_0x1F[22] & 0x1000) == 0x1000
        led_mode_enum = LedMode.ON_DEMAND if led_mode_bit_set else LedMode.CONTINUOUS
        self.j_config["led"]["mode"] = dict()
        self.j_config["led"]["mode"]["value"] = led_mode_enum.name

        #LED off time
        led_off_time = (self.tid_0x08_to_0x1F[22] >> 5) & 0x0005
        led_off_time = (led_off_time + 1) << 1
        self.j_config["led"]["offTime"] = dict()
        self.j_config["led"]["offTime"]["value"] = led_off_time

        #LED on time
        led_on_time = self.tid_0x08_to_0x1F[22] & 0x001F
        led_on_time = 10 * (led_on_time + 1)
        self.j_config["led"]["onTime"] = dict()
        self.j_config["led"]["onTime"]["value"] = led_on_time

        #FingerSpot enabled
        finger_spot_enabled = (self.tid_0x08_to_0x1F[0] & 0x1000) == 0x1000
        self.j_config["fingerSpot"] = dict()
        self.j_config["fingerSpot"]["enabled"] = finger_spot_enabled

        #FingerSpot for logger arming
        finger_spot_for_logger_arming = (self.tid_0x08_to_0x1F[0] & 0x0008) == 0x0008
        self.j_config["fingerSpot"]["useForLoggerArming"] = finger_spot_for_logger_arming

        #AntiTamper enabled
        anti_tamper_enabled = (self.tid_0x08_to_0x1F[0] & 0x0400) == 0x0400
        self.j_config["antiTamper"] = dict()
        self.j_config["antiTamper"]["enabled"] = anti_tamper_enabled

        #AntiTamper polarity
        anti_tamper_bit_set = (self.tid_0x08_to_0x1F[0] & 0xF7FF) == 0xF7FF
        anti_tamper_polarity_enum = AntiTamperPolarity(1 if anti_tamper_bit_set else 0)
        self.j_config["antiTamper"]["polarity"] = dict()
        self.j_config["antiTamper"]["polarity"]["value"] = anti_tamper_polarity_enum.name

        return True
        
    def to_reduced_config_dict(self):
        d = dict()
        d["logging"] = { }
        d["logging"]["interval"] = self.j_config["logging"]["interval"]["value"]
        d["logging"]["units"] = self.j_config["logging"]["interval"]["units"]
        d["logging"]["delayedStart"] = self.j_config["logging"]["delayedStart"]["value"]
        d["logging"]["numberOfSamples"] = self.j_config["logging"]["numberOfSamples"]["value"]
        d["temperatureLowerLimit"] = { }
        d["temperatureLowerLimit"]["limit"] = self.j_config["temperatureLimits"]["lowerLimit"]["value"]
        d["temperatureLowerLimit"]["alarmDelay"] = self.j_config["temperatureLimits"]["lowerLimit"]["alarmDelay"]["value"]
        d["temperatureUpperLimit"] = { }
        d["temperatureUpperLimit"]["limit"] = self.j_config["temperatureLimits"]["upperLimit"]["value"]
        d["temperatureUpperLimit"]["alarmDelay"] = self.j_config["temperatureLimits"]["upperLimit"]["alarmDelay"]["value"]
        d["led"] = { }
        d["led"]["enabled"] = self.j_config["led"]["enabled"]
        d["led"]["mode"] = self.j_config["led"]["mode"]["value"]
        d["led"]["offTime"] = self.j_config["led"]["offTime"]["value"]
        d["led"]["onTime"] = self.j_config["led"]["onTime"]["value"]
        d["fingerSpot"] = { }
        d["fingerSpot"]["enabled"] = self.j_config["fingerSpot"]["enabled"]
        d["fingerSpot"]["useForLoggerArming"] = self.j_config["fingerSpot"]["useForLoggerArming"]
        d["antiTamper"] = { }
        d["antiTamper"]["enabled"] = self.j_config["antiTamper"]["enabled"]
        d["antiTamper"]["polarity"] = self.j_config["antiTamper"]["polarity"]["value"]
        return d
    
#--------------------- STATUS

class RtcBasedTime:
    def number_of_seconds_after_start(self):
        # Opus RTC counts up every 30 seconds
        return 30 * self.number_of_rtc_cycles

    def to_date_time(self):
        if self.arm_time == None:
            return None
        else:
            return self.arm_time + timedelta(0, self.number_of_seconds_after_start())

    def utc_seconds_to_datetime(msb, lsb):
        return datetime.fromtimestamp(((msb & 0x7FFF) << 16) | (lsb & 0xFFFF), timezone.utc)

    #msb and lsb are RTC 30 second cycles
    def __init__(self, arm_time, msb, lsb):
        self.arm_time = arm_time
        self.number_of_rtc_cycles = ((msb & 0x00FF) << 16) | (lsb & 0xFFFF)

class State(Enum):
    SLEEP = 0
    STANDBY = 1
    INTERNAL_02 = 2
    READY = 3
    ARMED = 4
    BAP_MODE = 5
    LOGGING = 6
    FINISHED = 7
    INTERNAL_08 = 8
    INTERNAL_09 = 9
    INTERNAL_10 = 10
    INTERNAL_11 = 11
    INTERNAL_12 = 12
    INTERNAL_13 = 13
    INTERNAL_14 = 14
    INTERNAL_15 = 15
    INTERNAL_16 = 16
    INTERNAL_17 = 17
    INTERNAL_18 = 18
    INTERNAL_19 = 19
    INTERNAL_20 = 20
    INVALID = 21
    def state_from_user_bank_to_enum(user_word_0x05):
        if user_word_0x05 < 0 or user_word_0x05 > 20:
            return State.INVALID
        else:
            return State(user_word_0x05 & 0x001F)
    def state_from_packet_pc_to_enum(packet_pc):
        return State((packet_pc & 0x00E0) >> 5)

class TagId():
    def __init__(self):
        self.valid = False
        self.error_msg = ""
        self.EPC = None
        self.TID = None
        
    def to_dict(self):
        d = dict()
        d["TID"] = self.TID
        d["EPC"] = self.EPC
        return d

class TagIdZebraIOTC(TagId):
    def __init__(self, jdata):
        super().__init__()
        # These fields were checked when the data arrived from the radio so there is no need to check again
        self.valid = True
        self.TID = jdata["data"]["accessResults"][0].upper()
        self.EPC = jdata["data"]["idHex"].upper()

class Inventory:
    def __init__(self):
        self.valid = False
        self.error_msg = ""
        self.timestamp = None
        self.tid_0x08_0x1F = None
        self.user_0x00_0x07 = None
        self.state = None
        self.arm_time = None
        self.rtc = None
        self.next_sample = None
        self.temperature = None
        self.battery_present = None
        self.battery_voltage = None
        self.sensor_code = None
        self.on_chip_rssi = None
        self.channel = None
        self.rssi = None
        self.packet_pc_hex_string = None
        self.packet_pc_int = None
        self.xpc1_hex_string = None
        self.xpc1_int = None
        self.reader_host = None
        self.reader_mac = None

    def to_dict(self):
        d = dict()
        d["timestamp"] = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")   # "2024-12-25T12:07:44.345000Z"
        d["state"] = self.state.name                                        # "LOGGING"
        d["rtc"] = None if self.rtc == None else  self.rtc.to_date_time().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # "2024-12-25T12:07:44.345000Z"
        d["nextSample"] = self.next_sample      # 15
        d["temp"] = self.temperature            # 23.21
        d["battPresent"] = self.battery_present # True
        d["battVoltage"] = self.battery_voltage # 3.102
        d["sensorCode"] = self.sensor_code      # 125
        d["onChipRSSI"] = self.on_chip_rssi     # 18
        d["channel"] = self.channel             # 905250
        d["RSSI"] = self.rssi                   # -56.0
        d["packetPC"] = self.packet_pc_string   # "3F00"
        d["XPC_W1"] = self.xpc1_hex_string      # "0424"
        d["readerHost"] = self.reader_host      # "FX9600F10AE0"
        d["readerMAC"] = self.reader_mac        # "84:24:8D:EE:2A:E8"
        return d

class InventoryZebraIOTC(Inventory):
    def __init__(self, jdata):
        super().__init__()
        try:
            ts = jdata["timestamp"]
            self.timestamp = datetime.fromisoformat(ts[:len(ts)-2]+':'+ts[len(ts)-2:]) #translate to ISO UTC
            self.packet_pc_string = jdata["data"]["PC"].upper()
            self.packet_pc_int = int(self.packet_pc_string, 16)
            self.xpc1_hex_string = jdata["data"]["XPC1"].upper()
            self.xpc1_int = int(self.xpc1_hex_string, 16) 
            self.tid_0x08_0x1F = hex_string_to_ushort_array(jdata["data"]["accessResults"][1])
            self.user_0x00_0x07 = hex_string_to_ushort_array(jdata["data"]["accessResults"][2])
            self.state = State.state_from_user_bank_to_enum(self.user_0x00_0x07[5])
            self.next_sample = self.tid_0x08_0x1F[0x1B-0x08] & 0x1FFF
            if self.state in [State.READY, State.ARMED, State.BAP_MODE, State.LOGGING, State.FINISHED]:
                self.arm_time = RtcBasedTime.utc_seconds_to_datetime(self.tid_0x08_0x1F[0x11-0x08], self.tid_0x08_0x1F[0x12-0x08])
                self.rtc = RtcBasedTime(self.arm_time, self.user_0x00_0x07[7], self.user_0x00_0x07[6])
            else:
                self.rtc = None
                #if there is timestamp != 0 or logger counter != 0 or there is an alarm
                if self.tid_0x08_0x1F[0x11-0x08] != 0 or self.tid_0x08_0x1F[0x12-0x08] != 0 or self.next_sample != 0 or (self.packet_pc_int & 0x0007) != 0 or (self.xpc1_int & 0x0800) != 0:
                    self.arm_time = RtcBasedTime.utc_seconds_to_datetime(self.tid_0x08_0x1F[0x11-0x08], self.tid_0x08_0x1F[0x12-0x08])
                else:
                    self.arm_time = None     
            self.battery_present = (self.packet_pc_int & 0x0010) == 0x0010
            self.sensor_code = self.user_0x00_0x07[0] & 0x01FF
            self.on_chip_rssi = self.user_0x00_0x07[1] & 0x001F
            if self.on_chip_rssi > 30: # TODO: Fine tune maximum value
                self.temperature = None
                self.battery_voltage = None
            else:
                self.temperature = round(int.from_bytes(self.user_0x00_0x07[2].to_bytes(2,'big'), byteorder='big', signed=True) / 256.0, 2)
                self.battery_voltage = round(self.user_0x00_0x07[3] / 16000.0, 3)     
            self.channel = round(jdata["data"]["channel"] * 1000, 0)
            self.rssi = round(jdata["data"]["peakRssi"], 1)
            self.reader_host = jdata["data"]["hostName"]
            self.reader_mac = jdata["data"]["MAC"]
        except:
            self.valid = False
            self.error_msg = "ERROR: Opus.py-InventoryZebraIOTC(), " + str(jdata)

        else:
            self.valid = True

class LoggerArming():
    def __init__(self, inventory):
        self.error_number = 0
        self.error_message = None
        self.finger_spot_timestamp = None # For this application it is assumed that the FS is not used for the logger arming
        if inventory.state in [State.READY, State.ARMED, State.LOGGING, State.BAP_MODE, State.FINISHED]:
            self.successful = True
            self.timestamp = inventory.arm_time
        else:
            self.successful = False
            self.timestamp = None

    def to_dict(self):
        d = dict()
        d["successful"] = self.successful
        d["errorNumber"] = self.error_number
        d["errorMessage"] = self.error_message
        d["timestamp"] = None if self.timestamp == None else  self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        d["fingerSpotTimestamp"] = None if self.finger_spot_timestamp == None else  self.finger_spot_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") 
        return d

class Alarm(Enum):
    TEMPERATURE = 0
    HIGH_TEMPERATURE = 1
    LOW_TEMPERATURE = 2
    LOW_BATTERY = 3
    INITIAL_LOW_BATTERY = 4
    TAMPER = 5
    def get_alarms_in_str(packet_pc = 0, xpc_w1 = 0, tid_0x10 = 0):
        alarms = []
        if (packet_pc & 0x0001 == 0x0001) or (tid_0x10 & 0x0004 == 0x0004):
            alarms.append(Alarm.TAMPER.name)
        if (packet_pc & 0x0002 == 0x0002) or (tid_0x10 & 0x0008 == 0x0008):
            alarms.append(Alarm.LOW_BATTERY.name)
        if packet_pc & 0x0004 == 0x0004:
            alarms.append(Alarm.TEMPERATURE.name)
        if xpc_w1 & 0x0800 == 0x0800:
            alarms.append(Alarm.INITIAL_LOW_BATTERY.name)
        if tid_0x10 & 0x0001 == 0x0001:
            alarms.append(Alarm.LOW_TEMPERATURE.name)
        if tid_0x10 & 0x0002 == 0x0002:
            alarms.append(Alarm.HIGH_TEMPERATURE.name)
        return alarms
    def get_alarms_in_enum(packet_pc = 0, xpc_w1 = 0, tid_0x10 = 0):
        alarms = []
        if (packet_pc & 0x0001 == 0x0001) or (tid_0x10 & 0x0004 == 0x0004):
            alarms.append(Alarm.TAMPER)
        if (packet_pc & 0x0002 == 0x0002) or (tid_0x10 & 0x0008 == 0x0008):
            alarms.append(Alarm.LOW_BATTERY)
        if packet_pc & 0x0004 == 0x0004:
            alarms.append(Alarm.TEMPERATURE)
        if xpc_w1 & 0x0800 == 0x0800:
            alarms.append(Alarm.INITIAL_LOW_BATTERY)
        if tid_0x10 & 0x0001 == 0x0001:
            alarms.append(Alarm.LOW_TEMPERATURE)
        if tid_0x10 & 0x0002 == 0x0002:
            alarms.append(Alarm.HIGH_TEMPERATURE)
        return alarms

class Alarms():
    def __init__(self, config, inventory):
        self.alarms = Alarm.get_alarms_in_enum(inventory.packet_pc_int, inventory.xpc1_int, inventory.tid_0x08_0x1F[0x10-0x08])
        self.alarms_string = Alarm.get_alarms_in_str(inventory.packet_pc_int, inventory.xpc1_int, inventory.tid_0x08_0x1F[0x10-0x08])
        
        if inventory.arm_time != None: # It is always different from None if there is an alarm
            arm_time_in_sec = round(inventory.arm_time.timestamp())
            log_period_in_sec = config.log_interval.period_in_seconds()
            start_delay_in_periods = config.num_delayed_start_periods
        
        #Temperature Alarm
        if Alarm.TEMPERATURE in self.alarms or Alarm.HIGH_TEMPERATURE in self.alarms or Alarm.LOW_TEMPERATURE in self.alarms:
            self.temp_violation_value = None #TODO: Implement this feature
            alarm_address = inventory.tid_0x08_0x1F[0x0B-0x08] & 0x0FFF
            utc_sec = arm_time_in_sec + (log_period_in_sec * (alarm_address + start_delay_in_periods))
            self.temp_violation_timestamp = datetime.fromtimestamp(utc_sec, timezone.utc)
        else:
            self.temp_violation_value = None
            self.temp_violation_timestamp = None
        
        #Tamper Alarm
        if Alarm.TAMPER in self.alarms:
            alarm_address = inventory.tid_0x08_0x1F[0x0C-0x08] & 0x0FFF
            utc_sec = arm_time_in_sec + (log_period_in_sec * (alarm_address + start_delay_in_periods))
            self.tamper_violation_timestamp = datetime.fromtimestamp(utc_sec, timezone.utc)
        else:
            self.tamper_violation_timestamp = None
        
        #Battery Alarm
        if Alarm.LOW_BATTERY in self.alarms or Alarm.INITIAL_LOW_BATTERY in self.alarms:
            alarm_address = 0 if inventory.next_sample == 0 else inventory.next_sample - 1
            utc_sec = arm_time_in_sec + (log_period_in_sec * (alarm_address + start_delay_in_periods))
            self.battery_violation_timestamp = datetime.fromtimestamp(utc_sec, timezone.utc)
        else:
            self.battery_violation_timestamp = None

    def to_dict(self):
        d = dict()
        d["alarms"] = self.alarms_string
        d["temperatureViolationTimestamp"] = None if self.temp_violation_timestamp == None else self.temp_violation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        d["temperatureViolationValue"] = None #TODO: Implement
        d["tamperViolationTimestamp"] = None if self.tamper_violation_timestamp == None else  self.tamper_violation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        d["batteryAlarmTimestamp"] = None if self.battery_violation_timestamp == None else  self.battery_violation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") 
        return d

class LoggedData():
    def __init__(self):
        self.data = array.array('H', [])
        self.arm_time = None
        self.log_period_in_seconds = None
        self.log_delay = 0
        self.first_sample_number = 0

    def to_dict(self):
        a = []
        if len(self.data) == 0:
            return a
        timestamp = self.arm_time + timedelta(0, self.log_period_in_seconds * (self.log_delay + self.first_sample_number))
        for sample in self.data:
            d = dict()
            d["timestamp"] = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            d["temp"] = round(int.from_bytes(sample.to_bytes(2,'big'), byteorder='big', signed=True) / 256.0, 2)
            d["tamper"] = sample & 0x0001 == 0x0001
            a.append(d)
            timestamp += timedelta(0, self.log_period_in_seconds)
        return a

class Status:
    def __init__(self):
        self.version = "1.0.0"
        self.valid = False
        self.error_msg = ""
        self.tag_id = None
        self.inventories = None
        self.logger_config = None
        self.logger_arming = None
        self.logger_alarms = None
        self.logged_data = None

    def add_status(self, new_sts, delete_old_inventories = False):
        if delete_old_inventories:
            self.inventories = new_sts.inventories
        else:
            self.inventories.append(new_sts.inventories[0])
        self.logger_config = new_sts.logger_config
        self.logger_arming = new_sts.logger_arming
        self.logger_alarms = new_sts.logger_alarms

    def to_dict(self):
        d = dict()
        d["version"] = self.version
        d["tagID"] = self.tag_id.to_dict()
        d["inventories"] = []
        for i in self.inventories:
            d["inventories"].append(i.to_dict())
        d["loggerConf"] = self.logger_config.to_reduced_config_dict()
        d["loggerArming"] = self.logger_arming.to_dict()
        d["loggerAlarms"] = self.logger_alarms.to_dict()
        d["loggedData"] = self.logged_data.to_dict()
        return d

class StatusZebraIOTC(Status):
    def __init__(self, jdata):
        super().__init__()

        self.tag_id = TagIdZebraIOTC(jdata)
        if not self.tag_id.valid:
            self.error_msg = self.tag_id.error_msg
            self.valid = False
            return

        self.inventories = [InventoryZebraIOTC(jdata)]
        if not self.inventories[0].valid:
            self.error_msg = self.inventories[0].error_msg
            self.valid = False
            return        
        
        self.logger_config = Configuration(self.inventories[0].tid_0x08_0x1F)
        if not self.logger_config.valid:
            self.error_msg = self.logger_config.error_msg
            self.valid = False
            return 

        self.logger_arming = LoggerArming(self.inventories[0])
        self.logger_alarms = Alarms(self.logger_config, self.inventories[0])
        self.logged_data = LoggedData()

        self.valid = True
        
#-------------------- SELF TEST
def TestConfig1():
    c = Configuration()
    #a = json.dumps(c.j_config)
    a = c.tid_0x08_to_0x1F
    print(a)
    #w = c.get_reduced_json_config()

    a= 1

def json_from_reader_find_tags():
    j = """
    {
        "data": {
            "MAC": "84:24:8D:F1:0A:E0",
            "PC": "3f17",
            "XPC1": "0424",
            "accessResults": [
                "e2c24500200000668534009c",
                "9100 02A0 0FB0 0000 0000 0000 0000 0030 0490 0000 0000 0000 0000 0000 0000 0000 0000 0000 1e08 0000 07d0 09c4 3004 0108",
                "0006 001d 1900 b3b0 0011 0000 0000 0000"
            ],
            "antenna": 1,
            "channel": 918.70000000000005,
            "eventNum": 63,
            "format": "uii",
            "hostName": "FX9600F10AE0",
            "idHex": "e2c24500200000668534009c",
            "peakRssi": -39
        },
        "timestamp": "2024-11-21T13:20:53.319-0600",
        "type": "SIMPLE"
    }
    """
    return json.loads(j)

def TestInventory():
    j = json_from_reader_find_tags()
    i = InventoryZebraIOTC(j)
    print(json.dumps(i.to_dict()))
    a = 5

def TestStatus():
    j = json_from_reader_find_tags()
    s = StatusZebraIOTC(j)
    print(json.dumps(s.to_dict()))
    a = 5
