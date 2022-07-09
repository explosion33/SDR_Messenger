from rtlsdr import RtlSdr
from scipy.signal import welch
import math
from Codec import Codec
from Tools import suppress_stdout
from matplotlib import pyplot


#filter range
#number of values between 0-1024 to include
low_filter = 500
high_filter = 525
peak_threshold = 12


class SSB():
    """
    A SSB AM reciever that utilizes a RTL-SDR USB Dongle
    designed to work with Mhz frequencies
    """
    def __init__(self, freq: float, gain: float=60, broadband: float=1e6, peak_deviation_threshold: float=10, sample_rate: float=2e6, correction: int=60) -> None:
        """
        Reciever() | creates a new SSB object
        freq | frequency to read on Hz
        gain | Antenna Gain
        sample_rate | frequencies around freq to sample (min 2E+6)
        correction  | frequency correction for poor quality recievers
        """
        self._sdr = RtlSdr()

        self._sdr.sample_rate = sample_rate
        self._sdr.center_freq = freq
        self._sdr.freq_correction = correction
        self._sdr.gain = gain

        self._broadband = broadband
        self._dev_thresh = peak_deviation_threshold

    def _get_antenna_data(self):
        samples = self._sdr.read_samples(5000)

        #decode complex values into frequencies and amplitudes
        freqs, amps = welch(samples, nfft=1024, fs=self._sdr.sample_rate/1e6, return_onesided=False)

        return dict(sorted(dict(zip(freqs, amps)).items()))
    
    def _trim_to_broadband(self, data: dict) -> dict:
        f_low  = 0 - (self._broadband/1e6)
        f_high = 0 + (self._broadband/1e6)

        out = {}

        for val in data.keys():
            if val >= f_low and val <= f_high:
                out[val] = data[val]
            
        return out

    def _has_peak(self, data: dict):
        amps = data.values()

        avg = 0
        for val in amps:
            avg += val
        avg /= len(amps)

        stdev = 0
        for val in amps:
            stdev += (val - avg)**2
        stdev /= len(amps)
        stdev = math.sqrt(stdev)

        far = 0
        for val in amps:
            d = abs(val - stdev)
            if d > far:
                far = d

        return far > self._dev_thresh

    def _graph_signal_data(self, data: dict, horiz=[]):
        freqs = list(data.keys())
        amps = list(data.values())

        for i in range(len(freqs)):
            freqs[i] += self._sdr.center_freq/1e6
        

        fig, ax = pyplot.subplots(1)
        ax.plot(freqs, amps)
        ax.axvline(x=self._sdr.center_freq/1e6, color="black")
        for val in horiz:
            ax.axhline(y=val, color="green")
        pyplot.show()

    def isHigh(self):
        data = self._get_antenna_data()
        trimmed = self._trim_to_broadband(data)

        return self._has_peak(trimmed)

class Messenger(SSB):
    def __init__(self, freq: float, gain: float = 60, broadband: float = 1e6, peak_deviation_threshold: float = 10, sample_rate: float = 2e6, correction: int = 60) -> None:
        super().__init__(freq, gain, broadband, peak_deviation_threshold, sample_rate, correction)

        self.high_pulse = 0
        self.low_pulse = 0
        self._message_callback = Messenger._default_callback

    def _read_pulse_length(self, total_pulses=20):
        num_highs = 0
        num_lows = 0
        avg_high = 0
        avg_low = 0
        while True:
            bits_high = 0
            while self.isHigh():
                bits_high += 1

            if bits_high >= 3:
                num_highs += 1
                avg_high += bits_high
            
            bits_low = 0
            while num_highs > 0 and not self.isHigh():
                bits_low += 1
            
            if bits_low >= 3:
                num_lows += 1
                avg_low += bits_low
            

            if num_highs + num_lows >= total_pulses:
                break

        # calculate average length of high / low pulse
        high_len = avg_high // num_highs
        low_len = avg_low // num_lows

        self.high_pulse = high_len
        self.low_pulse = low_len

        return high_len, low_len

    def _wait_for_sync_end(self):
        bits = []
        while True:
            num_highs = 0
            while self.isHigh():
                num_highs += 1
                if num_highs == self.high_pulse:
                    bits.append(True)
                    break
            
            num_lows = 0
            while not self.isHigh():
                num_lows += 1
                if num_lows == self.low_pulse:
                    bits.append(False)
                    break

            if len(bits) >= 2 and bits[-2] and bits[-1]:
                break

    def _read_frames(self):
        curr = False
        high_streak = 0
        low_streak = 0
        bits = []
        in_frame = False
        while True:
            val = self.isHigh()
            
            # detect a value change (manchester bit)
            if val != curr:
                if curr == True: #was high
                    low_streak = 0
                
                elif curr == False: #was low
                    high_streak = 0
                
                curr = not curr
                continue
            
            # count number of consequtive highs / lows 
            if val:
                high_streak += 1
            else:
                low_streak += 1
            
            # if number of highs and lows pass the threshold determined with
            # Messenger._read_pulse_length()
            # with a 2 bit leway
            if high_streak >= self.high_pulse-2 and low_streak >= self.low_pulse-2:
                if curr:
                    bits.append(False)
                else:
                    bits.append(True)
                high_streak = 0
                low_streak = 0

                if len(bits) >= 8 and bits[-8:] == [False, True, True, True, True, True, True, False]:
                    if not in_frame:
                        bits = []
                        in_frame = True
                    else:
                        self._message_callback(self._parse_message(bits[0:-8]))

                        in_frame = False
                        bits = []

    def _parse_message(self, bits):
        out = ""
        b = Codec.boolarr_to_str(bits)
        for i in range(0, len(b), 8):
            c = chr(int(b[i:i+8], 2))
            out += c
        
        return out

    def _default_callback(msg):
        print(msg)

    def start(self, pulse_widths: tuple[int, int] = None):
        if pulse_widths is None:
            print("waiting to sync...")
            self._read_pulse_length()
            self._wait_for_sync_end()
        
        else:
            self.high_pulse, self.low_pulse = pulse_widths

        print(f"synced | high_pulse={self.high_pulse}, low_pulse={self.low_pulse}")
        
        self._read_frames()
    
    def set_callback(self, callback):
        self._message_callback = staticmethod(callback)


def callback(msg):
    print(f"{msg}")


# original msgs function
# packed into Messenger Class
def msgs():
    rec = None
    rec = SSB(144.07e6, broadband=0.5e5, gain=30)

    print("reading")

    
    # read alternating 1s and 0s to determine pulse length for high and low
    num_highs = 0
    num_lows = 0
    avg_high = 0
    avg_low = 0
    while True:
        bits_high = 0
        while rec.isHigh():
            bits_high += 1

        if bits_high >= 3:
            num_highs += 1
            avg_high += bits_high
        
        bits_low = 0
        while num_highs > 0 and not rec.isHigh():
            bits_low += 1
        
        if bits_low >= 3:
            num_lows += 1
            avg_low += bits_low
        

        if num_highs + num_lows >= 20:
            break

    # calculate average length of high / low pulse
    high_len = avg_high // num_highs
    low_len = avg_low // num_lows

    # read individual bits from 0101 stream until 11 appears
    bits = []
    while True:
        num_highs = 0
        while rec.isHigh():
            num_highs += 1
            if num_highs == high_len:
                bits.append(True)
                break
        
        num_lows = 0
        while not rec.isHigh():
            num_lows += 1
            if num_lows == low_len:
                bits.append(False)
                break

        if len(bits) >= 2 and bits[-2] and bits[-1]:
            break

    
    print(f"synced: high={high_len}, low={low_len}")

    # read manchester data stream, reading framing flags and outputing messages
    # to console
    curr = False
    high_streak = 0
    low_streak = 0
    bits = []
    in_frame = False
    while True:
        val = rec.isHigh()
        if val != curr:
            if curr == True: #was high
                low_streak = 0
            
            elif curr == False: #was low
                high_streak = 0
            
            curr = not curr
            continue
            
        if val:
            high_streak += 1
        else:
            low_streak += 1
        
        #print(high_streak, low_streak)
        if high_streak >= high_len-2 and low_streak >= low_len-2:
            if curr:
                bits.append(False)
            else:
                bits.append(True)
            high_streak = 0
            low_streak = 0

            if len(bits) >= 8 and bits[-8:] == [False, True, True, True, True, True, True, False]:
                # frame marker
                if not in_frame:
                    bits = []
                    in_frame = True
                else:
                    bits = bits[0:-8]
                    print(bits)
                    out = ""
                    b = Codec.boolarr_to_str(bits)
                    for i in range(0, len(b), 8):
                        c = chr(int(b[i:i+8], 2))
                        out += c
                    
                    print(out)

                    in_frame = False
                    bits = []
    
    
def main():
    msgr = Messenger(144.07e6, broadband=0.5e5, gain=30)
    msgr.set_callback(callback)
    msgr.start()

if "__main__" in __name__:
    main()     