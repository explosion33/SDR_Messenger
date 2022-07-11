# SDR_Messenger
A messenger system for PTT SSB radio and an RTL_SDR radio

SDR_Messenger is a python code base for working with data communication over 2m/70cm SSB Radio

## Hardware
Currently the project is utilizing the NESDR SMART RTL_SDR radio, a usb dongle for decoding radio waves, to read incoming data as a reciever

as well as a gimmicky binary PTT encoder connected to a YAESU VX-6

**RTL_SDR Reciever**
![Picture of RTL_SDR Setup](https://github.com/explosion33/SDR_Messenger/blob/master/photos/nesdr.jpg)

**PTT Binary Encoder / Transmitter**
![Picture of Transmitter Setup](https://github.com/explosion33/SDR_Messenger/blob/master/photos/ptt.jpg)
![Picture of Transmitter Schematic](https://github.com/explosion33/SDR_Messenger/blob/master/photos/ptt_schema.jpg)

## Setup

Instructions for adding RTL_SDR dlls to path


## Process
The current process for sending messages has several steps to ensure the proper message is recieved on the other end

Transmitter
1. ~30 alternatiting pulses [high, low, high, low] are transmitted to allow the reciever to measure the clock rate of the transmitter
2. two high bits are sent out in a row [high, high] to let the reciever know message streams are ready to be sent
3. the message is inputted by the user, and converted into bits
4. the message is wrapped with start / end binary flags
4. the bits are encoded using manchester encoding
5. the bits are then transmitted to the reciever
6. the transmitter reverts to step 3

Reciever
1. ~10 of the alternating bits are read for the number of cycles they persist the reciever stores the number of cycles each signal is active for
2. the reciever then, using the known time of on vs off, waits to recieve the two on bits
3. the reciever runs in a loop, recording the message as it comes through
4. when the start FLAG is detected the reader discards all previous bits and continues recording
5. when the end FLAG is detected the reader parses the bits into text and sends it as input to the user provided callback function
6. the reader reverts to step 3

## Limitations
The projects main limitation is that of its transmission speed, at ~12bps its not all that impressive. In its current state the speed is limmited by
1. The speed of python, the reciever can only accurately read the bits at a rate of 25 cycles per second. I believe this will be improved with a faster language
2. The transmission setup is limited to 33 cycles per second max transmission rate, this is likely due to
  1. the speed of the onboard raspberry pi clock
  2. the switching speed of the mosfet
  3. the PTT capabilities of the radio

## Going Forward
Going forward I would like to fix the major limitations listed above.

I would like to start by
1. making a dedicated transmitter circuit capable of much higher switching speeds
2. rewriting the essential code in C to get faster loop times
3. researching using more portions of the amplitude wave, allowing more symbols for transmission and removing the need to use manchester encoding (RTZ encoding)
  1. this would require researching power modulation in a dedicated circuit and power loss over a distance
  2. would require more usefull peak detection, i.e. how tall a peak is from its maximum peak
  
I would also like to fix some other minor issues, such as encoding errors with characters who compose the end FLAG, `01111110`, such as `?a`

As well as adding new features such as parity bits, and message compression
