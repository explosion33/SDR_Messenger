class Codec():
    def decode_manchester(signal: list):
        out = []
        i = 1
        while i < len(signal):
            last = signal[i-1]
            curr = signal[i]

            if last != curr:
                i += 1
                if last:
                    out.append(True)
                else:
                    out.append(False)
            i += 1

        return out

    def encode_manchester(signal: list):
        out = []
        for val in signal:
            if val:
                out.append(True)
                out.append(False)
            else:
                out.append(False)
                out.append(True)

        return out

    def boolarr_to_str(signal: list):
        p = ""
        for val in signal:
            if val:
                p += "1"
            else:
                p += "0"
        
        return p
    
    def str_to_boolarr(signal: str):
        bits = []
        for val in signal:
            if val == '1':
                bits.append(True)
            else:
                bits.append(False)
        return bits
