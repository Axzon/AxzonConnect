
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

import array

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

def ushort_array_to_byte_array(short_array):
    sa = short_array[:]
    sa.byteswap()
    return bytearray(sa.tobytes())

def is_string_hex(stringInHex):
    try:
        n = int(stringInHex, 16)
        return True
    except:
        return False

# EPC Gen2 CRC-16 Algorithm
# Poly = 0x1021; Initial Value = 0xFFFF; XOR Output;
def crc16_from_byte_array(byte_array):
    crcVal = 0xFFFF
    for inputByte in byte_array:
        crcVal = crcVal ^ (inputByte << 8)
        for i in range(8):
            if ((crcVal & 0x8000) == 0x8000):
                crcVal = (crcVal << 1) ^ 0x1021
            else:
                crcVal = crcVal << 1    
        crcVal = crcVal & 0xFFFF
    crcVal = crcVal ^ 0xFFFF 
    return crcVal    

def crc16_from_ushort_array(ushort_array):
    return crc16_from_byte_array(ushort_array_to_byte_array(ushort_array))