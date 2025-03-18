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

from enum import Enum
import array
import RfidUtility

class TemperatureCalibration:
    def __init__(self, calWords):
        self.valid = False
        self.word8 = 0
        self.word9 = 0
        self.wordA = 0
        self.wordB = 0
        self.crc = 0
        self.code1 = 0
        self.code2 = 0
        self.temp1 = 0.0
        self.temp2 = 0.0
        self.version = 0
        self.slope = 0.0
        self.offset = 0.0

        if (calWords == None):
           return
        if (len(calWords) != 4):
           return
        
        self.word8 = calWords[0]
        self.word9 = calWords[1]
        self.wordA = calWords[2]
        self.wordB = calWords[3]

        if self.decode() == False:
            return

        # Calculate CRC-16 over non-CRC bytes to compare with stored CRC-16
        data_words = array.array('H', [self.word9, self.wordA, self.wordB])
        calculated_crc = RfidUtility.crc16_from_ushort_array(data_words)

        # Determine if calibration is valid
        if  (self.crc == calculated_crc) and (self.code2 != self.code1) and (self.temp1 != self.temp2):
            self.slope = (self.temp2 - self.temp1) / (self.code2 - self.code1)
            self.offset = self.temp1 - self.slope * self.code1
            self.valid = True
 
    def get_temperature_in_c(self, code):
        if self.valid:
            return self.slope * code + self.offset
        else:
            return null

    def get_temperature_in_f(self, code):
        if self.valid:
            return 9.0 * (self.slope * code + self.offset) / 5.0 + 32.0
        else:
            return null

    def decode(self):
        self.version = self.wordB & 0x00000003
        if self.version == 0:
            self.crc = self.word8 & 0xFFFF
            self.code1 = (self.word9 & 0xFFF0) >> 4
            self.code2 = ((self.wordA & 0x01FF) << 3) | ((self.wordB & 0xE000) >> 13)
            self.temp1 = 0.1 * (((self.word9 & 0x000F) << 7) | ((self.wordA & 0xFF80) >> 9)) - 80.0
            self.temp2 = 0.1 * ((self.wordB & 0x1FFC) >> 2) - 80.0
            return True
        else:
            return False
