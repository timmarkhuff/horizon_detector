import pigpio
import bitarray as ba
import bitarray.util as bau
import time

#PACKET REFERENCE

#  UART packet          UART packet 2
#                                Parity
# ┌─┬──────┬─┬──┐      ┌─┬──────┬─┬──┐
# │1│Data  │P│00├─────►│1│Data  │P│00├─────►
# └─┴──────┴─┴──┘      └─┴──────┴─┴──┘
#  0 1-8    9 10,11     0 1-8    9 10,11


#   │      │             │    │   │
#   │ 0-7  │             │8-10│0-4│

#   -All bits are inverted (UART bits are shown inverted)
#   -UART is 100k baud, two stop bits, even parity (odd after inversion)
#   -SBus Data 11 bits per channel
#   -SBus Data comes in Big-Endian (most significant bit first)
#   -But 11 Bit number is Little-Endian!
#   -Example:
#       Data Packet:
#           11000010 100
#       Now Invert:
#           00111101 011
#       Above is *little-endian*, so the '1' on the right is 1024 in decimal. To read little-endian, reverse the bits and read left-to-right
#            110 00111101
#       In Decimal
#            1597




#minimum time between packets in microseconds (6000 microseconds is a typical gap, but the code looks for 5000 or *more*, in case there is some timing error)
_PACKET_BOUNDRY_TIME = 5000 

#in bits
_PACKET_LENGTH = 298
_UART_FRAME_LENGTH = 12 

#used to check packets for validity
_UART_FRAME_CONFORMANCE_BITMASK = ba.bitarray('100000000011')

#used to check failsafe status
_FAILSAFE_STATUS_BITMASK = ba.bitarray('000000001100')

_last_tick = 0 #last tick at which we received a state change
_working_packet_ptr = 0 #current bit in the working packet which we are waiting for data at
_working_packet = bau.zeros(_PACKET_LENGTH) #stores result as packet comes into system


_latest_complete_packet = bau.zeros(_PACKET_LENGTH) #stores the last packet that the system recorded
_latest_complete_packet_timestamp = 0 #stores tick at which the packet was recorded
_is_connected = False #True if receiver is getting transmission, False if not connected



def _sanity_check_packet(packet):
    #checks for data coherency for UART frames
    #sbus is an *inverted* protocol

    #Returns 3 value tuple:
        # 1 - Packet good? - True/False
        # 2 - Error - None if no error, error message if packet is bad
        # 3 - Data - None if no error, bad packet data if packet is bad

    ret_val = (True,None,None)

    #SBus starts with an opening byte (0x0F), which we ignore
    #UART frames are 12 bits (see packet diagram above)
    #22-bytes of data + 1 end byte with failsafe data
    
    for packet_bits_ptr in range (_UART_FRAME_LENGTH,_UART_FRAME_LENGTH+23*_UART_FRAME_LENGTH,_UART_FRAME_LENGTH):

        #extract current UART frame
        cur_UART_frame =  packet[packet_bits_ptr:packet_bits_ptr+_UART_FRAME_LENGTH]

        #this "and" operation will result in 100000000000 in binary for correct frame - 2048 decimal
        if bau.ba2int(_UART_FRAME_CONFORMANCE_BITMASK & cur_UART_frame) != 2048:
            return (False,f'UART start or stop bits bad (frame #{packet_bits_ptr/_UART_FRAME_LENGTH+1})', cur_UART_frame)
        
        #parity bit in UART 
        if bau.parity(cur_UART_frame[1:9]) == cur_UART_frame[9]:
            #due to inversion, parity checks fail when parity is equal
            return (False,f'Parity check failure (frame #{packet_bits_ptr/_UART_FRAME_LENGTH+1})', cur_UART_frame )
    
    return ret_val

def _on_change(gpio,level,tick):
    #pigpio calls this method whenever it detects a level change
    global _last_tick, \
        _working_packet, \
        _working_packet_ptr, \
        _latest_complete_packet, \
        _latest_complete_packet_timestamp, \
        _is_connected

    time_elapsed = tick - _last_tick

    if time_elapsed < 0:
        #the current tick wraps around once it exceeds 32-bit unsigned or 4294967295.
        #PIGPIO docs says this happens about once every 71 minutes
        #handle this case
        time_elapsed = 4294967295 - _last_tick + tick

    if time_elapsed >= _PACKET_BOUNDRY_TIME:
        #if we are here then this method was triggered by the first "one" of this new packet
        #and we have just completed a frame boundry
        
        if (_sanity_check_packet(_working_packet)[0]):
            #only set _latest_complete_packet if it passes sanity check,
            #otherwise leave old value there
            _latest_complete_packet, _working_packet = _working_packet, _latest_complete_packet
            _latest_complete_packet_timestamp = tick

            #SBus transmits transmission status in bits 279 and 280 (failsafe), high is connected
            _is_connected = bau.ba2int(_latest_complete_packet[279:281]) == 3
            

        #reset working packet to accept the new packet data
        _working_packet.setall(0)
        _working_packet_ptr = 0

        #start timing to interpret next bit
        _last_tick = tick 
        return
    
    num_bits = round((time_elapsed)/10) #10 microseconds per data bit, so number of bits since last state change is time difference/10
    bit_val = bool(-level+1) #enter the level *before* this state change which is the inverse of current change.
    
    #record number of bits at the level since the state changed

    #advance ptr to insert correct number of bits
    new_working_packet_ptr = _working_packet_ptr+num_bits
    _working_packet[_working_packet_ptr:new_working_packet_ptr] = bit_val
    _working_packet_ptr = new_working_packet_ptr

    #start timing to interpret next bit
    _last_tick = tick


class SbusReader:
    def __init__(self, gpio_pin):
        self.gpio_pin = gpio_pin #BCM pin
        self.pi = pigpio.pi()
        self.pi.set_mode(gpio_pin, pigpio.INPUT)
    
    def begin_listen(self):
        global _latest_complete_packet_timestamp
        self.pi.callback(self.gpio_pin, pigpio.EITHER_EDGE, _on_change)
        _latest_complete_packet_timestamp = self.pi.get_current_tick()
    
    def end_listen(self):
        self.pi.stop()
    
    def translate_packet(self,packet):
        #ASSUMES packet has been sanity checked.
        channel_bits = ba.bitarray(176) #holds the bits of the 16 11-bit channel values
        channel_bits.setall(0)

        channel_bits_ptr = 0

        #22 bytes of data hold 16 channel 11-bit values
        #skip first frame, it is an SBUS start frame
        for packet_bits_ptr in range (_UART_FRAME_LENGTH,_UART_FRAME_LENGTH+22*_UART_FRAME_LENGTH,_UART_FRAME_LENGTH):
            #extract from UART frame and invert each byte
            channel_bits[channel_bits_ptr:channel_bits_ptr+8]=~packet[packet_bits_ptr+1:packet_bits_ptr+9]
            channel_bits_ptr += 8

        ret_list = []
        for channel_ptr in range(0,16*11,11):
            #iterate through 11-bit numbers, converting them to ints. Note little endian.
            ret_list.append(bau.ba2int(ba.bitarray(channel_bits[channel_ptr:channel_ptr+11],endian='little')))
        
        return ret_list

    def retrieve_latest_packet(self):
        return _latest_complete_packet
    
    def translate_latest_packet(self):
        return self.translate_packet(_latest_complete_packet)

    def display_latest_packet(self):
        #calling this function right after begin_listen will fail - no packet has had time to completely reach the receiver
        #use time.sleep(.1) first
        channel_val_list = self.translate_latest_packet()
        for i,val in enumerate(channel_val_list):
            print(f'Channel #{i+1}: {val}')
        print(f'Packet Age(milliseconds): {self.get_latest_packet_age()}')
        
        transmission_status = ''
        if(_is_connected):
            transmission_status = 'CONNECTED'
        else:
            transmission_status = 'DISCONNECTED'
        
        print(f'Transmission Status: {transmission_status}')
    
    def get_latest_packet_age(self):
        #in milliseconds
        return int((self.pi.get_current_tick() - _latest_complete_packet_timestamp)/1000)
    
    def is_connected(self):
        return _is_connected

    #Uses curses library to display all channel data in static screen
    #Note this is a blocking call - no other code will execute until the user
    #exits the screen by pressing a key.
    def _display_latest_packet_curses(self, stdscr):
        import curses
        
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

        stdscr.clear()
        stdscr.nodelay(True)
        curses.curs_set(0)
        
        while True:
            time.sleep(.05)
            try:
                key = stdscr.getkey()
            except:
                key = None
            finally:
                if key is not None:
                    curses.curs_set(1)
                    return
                try:
                    channelValList = self.translate_latest_packet()
                    for i,val in enumerate(channelValList):
                        stdscr.addstr(int(i/2), (i % 2)*25, f'Channel # {i+1}: {val}   ')
                    stdscr.addstr(8,0,f'Packet Age(milliseconds): {self.get_latest_packet_age()}        ')
                    if (_is_connected):
                        stdscr.addstr(9,0,'CONNECTED',curses.color_pair(1))
                        stdscr.addstr(9,9,'   ')
                    else:
                        stdscr.addstr(9,0,'DISCONNECTED',curses.color_pair(2))
                    
                    stdscr.addstr(10,0,'Press any key to stop.')
        
                    stdscr.refresh()
                except:
                    #restore cursor before throwing exception
                    curses.curs_set(1)
                    self.end_listen()
                    raise
                    

    def display_latest_packet_curses(self):
        from curses import wrapper
        wrapper(self._display_latest_packet_curses)