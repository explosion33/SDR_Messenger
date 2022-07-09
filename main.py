"""
TODO
better peak detection and focusing
    currently it is user tuned to a given range by the user
    a peak is detected using the scale between the maximum and minimum value

high / low duration determination
    currently just determine if the signal is high, need to be able to determine how long a signal is high
    need to filter out outliers by having a minumun high duration

data decoding
    need a way to decode binary data from the highs and lows
    perhaps a start / end sequence or just string data
"""
from rtlsdr import RtlSdr
import time
from scipy.signal import welch

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2e6  # Hz
sdr.center_freq = 144.1e6     # Hz
sdr.freq_correction = 60   # PPM
sdr.gain = 60

#filter range
#number of values between 0-1024 to include
low_filter = 500
high_filter = 525
peak_threshold = 12


last = time.time()
isHigh = False
while True:
    samples = sdr.read_samples(5000)

    #decode complex values into frequencies and amplitudes
    freqs, amps = welch(samples, nfft=1024, fs=sdr.sample_rate/1e6)

    #compile and sort values
    vals = {}
    for i in range(len(freqs)):
        vals[freqs[i]] = amps[i]


    vals = dict(sorted(vals.items()))

    #shrink amplitude values around where thte peak should be
    #servers to only include SSB instead of FM broadband 
    amps = list(vals.values())[low_filter:high_filter]

    #find max / min value among peak frequency
    high = None
    low = None
    for val in amps:
        if high is None or val > high:
            high = val
        if low is None or val < low:
            low = val

    #scaler between high and low (peak determination)
    offset = high/low


    if offset > peak_threshold:
        if not isHigh:
            t = time.time() - last
            #print("high, dt =", t)
            isHigh = True

            last = time.time()
    elif isHigh:
        t = time.time() - last
        if t > 0.05:
            print("high, dt =", t)

        last = time.time()
        isHigh = False