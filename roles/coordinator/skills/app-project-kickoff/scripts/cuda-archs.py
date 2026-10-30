"""List the CUDA compute capabilities compiled into a fatbin-carrying DLL (e.g. ggml-cuda.dll).

Usage: python cuda-archs.py <path to dll>
Prints e.g. [('ptx', 75), ('sass', 75), ...]. 75 = Turing (RTX 20), 86 = Ampere (RTX 30),
89 = Ada (RTX 40), 120 = Blackwell (RTX 50). A 'sass' entry runs natively; 'ptx' only is JIT-compiled
by the driver for newer GPUs.
"""
import struct
import sys

FATBIN_MAGIC = struct.pack("<I", 0xBA55ED50)


def archs(data: bytes) -> set:
    found, i = set(), 0
    while (i := data.find(FATBIN_MAGIC, i)) >= 0:
        header = struct.unpack_from("<H", data, i + 6)[0]
        size = struct.unpack_from("<Q", data, i + 8)[0]
        p, end = i + header, i + header + size
        while p < end and p + 32 < len(data):
            kind, _, entry_header, entry_size = struct.unpack_from("<HHIQ", data, p)
            found.add(("ptx" if kind == 1 else "sass", struct.unpack_from("<I", data, p + 28)[0]))
            if entry_header == 0:
                break
            p += entry_header + entry_size
        i += 4
    return found


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        print(sorted(archs(f.read())))
