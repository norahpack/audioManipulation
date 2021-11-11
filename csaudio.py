import IPython.display as ipd
import matplotlib.pyplot as plt
import numpy as np
import time
import wave
import os
import seaborn as sns
import sys

sns.set(style="darkgrid")
wave.big_endian = 0

def play(filename):
    """plays the file"""
    return ipd.Audio(filename)

#
# altplay( filename )   # in case play doesn't work!
#
# a useful thing to have... can be done all in sw under windows...
#
if os.name == 'nt':
    import winsound
elif os.uname()[0] == 'Linux':
    import ossaudiodev

def altplay(filename):
    """altplay(filename)    alternative audio player!

       (Before 2020, this was called "play") 
       This function plays a .wav file named filename (a string) 
       under Windows, Linux, or Mac.
       On a Mac, you no longer need to have the "play"
       application in the current folder (.) [that was MacOS pre-10.5]
    """
    if type(filename) != type(''):
        raise TypeError('filename must be a string when calling altplay(filename)')
    if os.name == 'nt':
        winsound.PlaySound(filename, winsound.SND_FILENAME)
    elif os.uname()[0] == 'Linux':
        os.system('/usr/bin/play ' + filename
          + ' || /usr/bin/aplay ' + filename)
    # If not a Windows or Linux machine, assume Mac.
    # If you're using another OS, you'll need to adjust this...
    else:
        # this was the pre MacOS 10.5 method...
        #os.system(('./play ' + filename))
        # now, it seems that /usr/bin/afplay is provided with MacOS X
        # and it seems to work in the same way play did
        # perhaps Apple simply used play?
        os.system(('/usr/bin/afplay ' + filename))

# this is what altplay _should_ be called! :-)
nowplay = altplay




# Functions for reading in the data.
# Initial call is to read_wav(filename), which in turn calls:
#     - get_data(filename), which pulls out the parameters and raw frames
#        of the sound file.
#     - These then get passed to tr(params, rf), which gets the list of floats
#        (sound_data) that hw3pr1.py runs all the list comprehensions on.
#
def tr(params, rf):
    """tr transforms raw frames (rf) to floating-point samples."""
    samps = [x for x in rf]    # convert to numeric bytes
    # give parameters nicer names
    nchannels = params[0]
    sampwidth = params[1]
    nsamples  = params[3]
    if sampwidth == 1:
        for i in range(nsamples):
            if samps[i] < 128:
                samps[i] *= 256.0       # Convert to 16-bit range, floating
            else:
                samps[i] = (samps[i] - 256) * 256.0

    elif sampwidth == 2:
        newsamps = nsamples * nchannels * [0]
        for i in range(nsamples * nchannels):
            # The wav package gives us the data in native
            # "endian-ness".  The clever indexing with wave.big_endian
            # makes sure we unpack in the proper byte order.
            sampval = samps[2*i + 1 - wave.big_endian] * 256 \
              + samps[2*i + wave.big_endian]
            if sampval >= 32768:
                sampval -= 65536
            newsamps[i] = float(sampval)
        samps = newsamps
    else:
        print('A sample width of', params[1], 'is not supported.',
          file = sys.stderr)
        print('Returning silence.', file = sys.stderr)
        samps = nsamples * [0.0]

    if nchannels == 2:
        # Mix to mono
        newsamps = nsamples * [0]
        for i in range(nsamples):
            newsamps[i] = (samps[2 * i] + samps[2 * i + 1]) / 2.0
        samps = newsamps
    return samps

def get_data(filename):
    """Read sound data from a named file.
       The file needs to be in .wav format.
       There are lots of conversion programs online, however,
       that can create .wav from .mp3 and other formats."""
    
    # This will complain if the file isn't there!
    fin = wave.open(filename, 'rb')
    params = fin.getparams()
    #printParams(params)
    rawFrames = fin.readframes(params[3])
    # Need to extract just one channel of sound data at the right width...
    fin.close()
    return params, rawFrames

def read_wav(filename):
    """read_wav reads the audio data from the file
       named "filename" and returns it as a pair (samples,
       sampling_rate).  "samples" is a list of the raw sound samples;
       "sampling_rate" is an integer giving the sampling rate in
       samples per second (typically 22050 or 44100).

       The samples are floating-point values in the range (-32768, 32767)."""
    
    sound_data = [42, 42]
    try:
        params, rf = get_data(filename)
        samps = tr(params, rf)
    except:
        print("There was a problem with the file", filename, file = sys.stderr)
        print("You might check if it's here and of", file = sys.stderr)
        print("the correct format (.wav) ... ", file = sys.stderr)
        return None # nothing

    numchannels = params[0]
    datawidth = params[1]
    framerate = params[2]
    numsamples = params[3]
    print(file = sys.stderr)
    print('You opened', filename, 'which has', file = sys.stderr)
    print('   ', numsamples, 'audio samples, taken at', file = sys.stderr)
    print('   ', framerate, 'hertz (samples per second).', file = sys.stderr)
    print(file = sys.stderr)
    sound_data[0] = samps
    sound_data[1] = framerate
    return sound_data


# Functions for printing data out.
# Call is to write_wav(sound_data, desired filename), which in turn calls:
#     - tri(params, data), which converts the float list into a bunch of bytes
#     - write_wav(params, rawframesstring, filename) which accepts the bytes
#        and converts them to a sound file
def tri(params, samps):
    """tri is tr inverse, i.e. from samples to raw frames"""
    if params[1] == 1:                 # one byte per sample
        samps = [int(x / 256 + 127.5) for x in samps]
        #print 'max, min are', max(samps), min(samps)
        rf = [chr(x) for x in samps]
    elif params[1] == 2:               # two bytes per sample
        bytesamps = (2*params[3])*[0]  # start at all zeros
        for i in range(params[3]):
            # maybe another rounding strategy in the future?
            intval = int(samps[i])
            if intval >  32767:
                intval = 32767
            if intval < -32767:
                intval = -32767  # maybe could be -32768
            if intval < 0:
                intval += 65536 # Handle negative values
            # The wav package wants its data in native "endian-ness".
            # The clever indexing with wave.big_endian makes sure we
            # pack in the proper byte order.
            bytesamps[2*i + 1 - wave.big_endian] = intval // 256
            bytesamps[2*i + wave.big_endian] = intval % 256
        samps = bytesamps
        #print 'max, min are', max(samps), min(samps)
        rf = [chr(x).encode("latin-1") for x in samps]
    return b''.join(rf)

def write_data(params = None, rawFrames = None, filename = "out.wav"):
    """Write data out to .wav format"""

    fout = wave.open(filename, 'wb')
    if params:
        fout.setparams(params)
        if rawFrames:
            fout.writeframes(rawFrames)
        else:
            print('no frames')
    else:
        print('no params')
    fout.close()

def write_wav(sound_data, filename = "out.wav"):
    """write_wav creates a .wav file whose contents are sound_data.
       sound_data is [audio data, sample_rate] as a list.

       The second parameter is the output file name.
       If no name is specified, this parameter defaults to 'out.wav'."""
    
    # first, make the sampling rate an int...
    sound_data[1] = int(sound_data[1])

    # then do some other checking
    if type(sound_data) != type([]) or \
      len(sound_data) < 2 or \
      type(sound_data[0]) != type([]) or \
      type(sound_data[1]) != type(42):
        print(
            """write_wav was called with a first argument,
            sound_data, that was _not_ an appropriate list.

            That argument needs to be a list such that
            sound_data[0] is the raw sound samples and
            sound_data[1] is the sampling rate, e.g.,

                [[d0, d1, d2, ...], sample_rate]

            where each d0, d1, d2, ... is a floating-point value
            in the range (-32768, 32767) and sample_rate is an
            integer representing the frequency at which audio
            samples were taken.""",
            file = sys.stderr
            )
        return None # nothing
    # name the two components of sound_data
    data = sound_data[0]
    sample_rate = sound_data[1]
    # compose the file...
    framerate = int(sample_rate)
    if framerate < 0:
        framerate = -framerate
    if framerate < 1:
        framerate = 1
    # always 1 channel and 2 output bytes per sample
    params = [1, 2, framerate, len(data), "NONE", "No compression"]
    # convert to raw frames
    rawframesstring = tri(params, data)
    write_data(params, rawframesstring, filename)
    print(file = sys.stderr)
    print('You have written the file', filename, 'which has', file = sys.stderr)
    print('   ', len(data), 'audio samples, taken at', file = sys.stderr)
    print('   ', sample_rate, 'hertz.', file = sys.stderr)
    print(file = sys.stderr)
    return # nothing

