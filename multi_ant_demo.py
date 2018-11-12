"""
    Code based on:
        https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/03-basicchannel.py
    in the python-ant repository and
        https://github.com/tomwardill/developerhealth
    by Tom Wardill
"""
import sys
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER
import binascii
from diskcache import Cache

class HeartrateCallback(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print('heartrate: received message')
            #print(len(msg.payload))
            hexValues = ''.join(['[{}] '.format(str(binascii.hexlify(b))) for b in msg.payload])
            #hexValues = binascii.hexlify(msg.payload)
            #print( "id:{} value:{} type:{}".format(message.number, hexValues, type(msg) ) )
            print(hexValues)
            cacheLocation = '/home/aws_cam/diskcachedir'
            with Cache(cacheLocation) as cache:
                cache[b'heartrate'] = ord(msg.payload[8])
                print('Cached heartrate: {}'.format(cache[b'heartrate']))

class TemperatureCallback(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print('Temperature: received message')
            #print(len(msg.payload))
            hexValues = ''.join(['[{}] '.format(str(binascii.hexlify(b))) for b in msg.payload])
            #hexValues = binascii.hexlify(msg.payload)
            #print( "id:{} value:{} type:{}".format(message.number, hexValues, type(msg) ) )
            print(hexValues)

            print('Temperature Page ID: {}'.format(ord(msg.payload[1])))

            if ord(msg.payload[1]) == 1:
                current_temperature = 32 + (1.8 * (0.01 * int(str(binascii.hexlify(msg.payload[8])) + str(binascii.hexlify(msg.payload[7])),16)))
                print('Current Page1 Temnperature: {}'.format(current_temperature))

                cacheLocation = '/home/aws_cam/diskcachedir'
                with Cache(cacheLocation) as cache:
                    cache[b'temperature'] = current_temperature
                    print('Cached temperature: {}'.format(cache[b'temperature']))


class CadenceCallback(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print('cadence: received message')
            #print(len(msg.payload))
            hexValues = ''.join(['[{}] '.format(str(binascii.hexlify(b))) for b in msg.payload])
            #hexValues = binascii.hexlify(msg.payload)
            #print( "id:{} value:{} type:{}".format(message.number, hexValues, type(msg) ) )
            print(hexValues)

            curr_cad_rev_count = int(str(binascii.hexlify(msg.payload[8])) + str(binascii.hexlify(msg.payload[7])), 16)
            print('Cadence Rev Count: {}'.format(curr_cad_rev_count))
            curr_cad_event_time = int(str(binascii.hexlify(msg.payload[6])) + str(binascii.hexlify(msg.payload[5])), 16)
            print('Cadence Event Time: {}'.format(curr_cad_event_time))

            #Stop bit doesn't seem to exist for the Garmin cadence sensor
            #print('Cadence Page ID: {} Stop Bit: {}'.format(ord(msg.payload[1]), ord(msg.payload[2])))

            cache_location = '/home/aws_cam/diskcachedir'

            with Cache(cache_location) as cache:
                prev_cad_rev_count = cache.get(b'prevcadrevcount', curr_cad_rev_count - 1)
                prev_cad_event_time = cache.get(b'prevcadevttime', curr_cad_event_time - 1)

                cache[b'prevcadrevcount'] = curr_cad_rev_count
                cache[b'prevcadevttime'] = curr_cad_event_time

                delta_cad_rev_count = curr_cad_rev_count - prev_cad_rev_count
                delta_cad_event_time = curr_cad_event_time - prev_cad_event_time

                print('Cadence Delta Rev Count: {} , Cadence Delta Evt Time: {}'.format(delta_cad_rev_count, delta_cad_event_time))

                #avoid divide-by-zero errors; only re-calculate speed if input values greater than zero

                if delta_cad_event_time > 0:
                    rpm = (delta_cad_rev_count * 60 * 1024)/delta_cad_event_time

                    print('Calc Cadence [RPM]: {}'.format(str(rpm)))
                    cache[b'cadence'] = str(rpm)
                    print('Cached cadence (modified): {} \n =====\n'.format(cache[b'cadence']))
                else:
                    #save as a string to return a Truthy value
                    cache[b'cadence'] = str(0)
                    print('Cached cadence (no new data): {} \n =====\n'.format(cache[b'cadence']))


class SpeedCallback(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print('speed: received message')
            #print(len(msg.payload))
            hexValues = ''.join(['[{}] '.format(str(binascii.hexlify(b))) for b in msg.payload])
            #hexValues = binascii.hexlify(msg.payload)
            #print( "id:{} value:{} type:{}".format(message.number, hexValues, type(msg) ) )
            print(hexValues)
            curr_speed_rev_count = int(str(binascii.hexlify(msg.payload[8])) + str(binascii.hexlify(msg.payload[7])), 16)
            print('Speed Rev Count: {}'.format(curr_speed_rev_count))
            curr_speed_event_time = int(str(binascii.hexlify(msg.payload[6])) + str(binascii.hexlify(msg.payload[5])), 16)
            print('Speed Event Time (1024): {}'.format(curr_speed_event_time))

            print('Speed Page ID: {} Stop Bit: {}'.format(ord(msg.payload[1]), ord(msg.payload[2])))

            stop_bit = ord(msg.payload[2])
            #Only update speed value when stop bit = 0 which means bike is moving

            cacheLocation = '/home/aws_cam/diskcachedir'

            if stop_bit == 0:

                with Cache(cacheLocation) as cache:
                    prev_speed_rev_count = cache.get(b'prevspdrevcount', curr_speed_rev_count - 1)
                    prev_speed_event_time = cache.get(b'prevspdevttime', curr_speed_event_time - 1)

                    cache[b'prevspdrevcount'] = curr_speed_rev_count
                    cache[b'prevspdevttime'] = curr_speed_event_time

                    delta_speed_rev_count = curr_speed_rev_count - prev_speed_rev_count
                    delta_speed_event_time = curr_speed_event_time - prev_speed_event_time

                    print('Delta Rev Count: {} , Delta Evt Time: {}'.format(delta_speed_rev_count, delta_speed_event_time))

                    #avoid divide-by-zero errors; only re-calculate speed if input values greater than zero

                    if delta_speed_rev_count > 0 and delta_speed_event_time > 0:
                        #736mm = 29 inch circumfrence wheel
                        calc_speed = (delta_speed_rev_count * 0.736 * 1024)/delta_speed_event_time
                        kmh = int((calc_speed * 60 * 60) / 1000)
                        print('Calc Speed [m/s]: {}, KMH: {}'.format(str(calc_speed), str(kmh)))
                        cache[b'speed'] = str(kmh)
                        print('Cached speed: {} \n =====\n'.format(cache[b'speed']))
            else:
                #Otherwise our speed is zero km/h (bike not moving)
                with Cache(cacheLocation) as cache:
                    cache[b'speed'] = str(0)
                    print('Cached speed: {} \n =====\n'.format(cache[b'speed']))


class HRM(event.EventCallback):

    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None
        self.channel2 = None
        self.channel3 = None
        self.channel4 = None

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(CadenceCallback())
        self.channel2.registerCallback(SpeedCallback())
        self.channel3.registerCallback(HeartrateCallback())
        self.channel4.registerCallback(TemperatureCallback())
        print("start listening for device events")

    def stop(self):
        if self.channel:
            self.channel.close()
            self.channel.unassign()

        if self.channel2:
            self.channel2.close()
            self.channel2.unassign()

        if self.channel3:
            self.channel3.close()
            self.channel3.unassign()

        if self.channel4:
            self.channel4.close()
            self.channel4.unassign()

        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver(self.serial)
        self.antnode = node.Node(stick)
        
        print('node running:{}'.format(self.antnode.running))
        #if self.antnode.running == False:
        self.antnode.start()
        print('Antnode capabilities-Channels: {}, Networks: {}').format(self.antnode.getCapabilities()[0], self.antnode.getCapabilities()[1])

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
        self.antnode.setNetworkKey(0, key)

        #Cadence channel
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:CAD'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(122, 0, 0)
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
	self.channel.setPeriod(8102)
        self.channel.setFrequency(57)
        self.channel.open()

        #Channel 2 - Speed
        self.channel2 = self.antnode.getFreeChannel()
        self.channel2.name = 'C:SPD'
        self.channel2.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel2.setID(123, 0, 0)
        self.channel2.setSearchTimeout(TIMEOUT_NEVER)
        self.channel2.setPeriod(8118)
        self.channel2.setFrequency(57) 
        self.channel2.open()

        #Channel 3  - Heartrate
        self.channel3 = self.antnode.getFreeChannel()
        self.channel3.name = 'C:HR'
        self.channel3.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel3.setID(120, 0, 0)
        self.channel3.setSearchTimeout(TIMEOUT_NEVER)
        self.channel3.setPeriod(8070)
        self.channel3.setFrequency(57)
        self.channel3.open()

        #Channel 4  - Temperature
        self.channel4 = self.antnode.getFreeChannel()
        self.channel4.name = 'C:TMP'
        self.channel4.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel4.setID(25, 0, 0)
        self.channel4.setSearchTimeout(TIMEOUT_NEVER)
        self.channel4.setPeriod(8192)
        self.channel4.setFrequency(57)
        self.channel4.open()

SERIAL = '/dev/ttyUSB0'
NETKEY = 'B9A521FBBD72C345'.decode('hex')

with HRM(serial=SERIAL, netkey=NETKEY) as hrm:
    hrm.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            cache_location = '/home/aws_cam/diskcachedir'
            with Cache(cache_location) as cache:
                cache[b'speed'] = 0
                cache[b'prevspdrevcount'] = 0
                cache[b'prevspdevttime'] = 0
                cache[b'prevcadrevcount'] = 0
                cache[b'prevcadevttime'] = 0
                cache[b'cadence'] = 0
                cache[b'heartrate'] = 0
                cache[b'temperature'] = 0

            sys.exit(0)
