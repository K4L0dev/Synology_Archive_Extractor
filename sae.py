# Based on synology source 

import ctypes
from enum import IntFlag
import argparse

_libcodesign = ctypes.CDLL("libsynocodesign.so")

# synoarchive_init funtion prototype
_synoarchive_init = _libcodesign.synoarchive_init
_synoarchive_init.argtypes = (ctypes.c_char_p,)
_synoarchive_init.restype = ctypes.c_void_p

# synoarchive_open_with_keytype funtion prototype
_synoarchive_open = _libcodesign.synoarchive_open_with_keytype
_synoarchive_open.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint)
_synoarchive_open.restype = ctypes.c_bool

# synoarchive_extract_multiple funtion prototype
_synoarchive_extract_multiple = _libcodesign.synoarchive_extract_multiple
_synoarchive_extract_multiple.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint)
_synoarchive_extract_multiple.restype = ctypes.c_bool

# synoarchive_free function prototype
_synoarchive_free = _libcodesign.synoarchive_free
_synoarchive_free.argtypes = (ctypes.c_void_p,)

class SynoArchiveFlags(IntFlag):
    OWNER= 1,
    PERM= 2,
    TIME= 4,
    NO_OVERWRITE= 8,
    UNLINK= 16,
    ACL= 32,
    FFLAGS= 64,
    XATTR= 128,
    NO_AUTODIR= 256,
    NO_OVERWRITE_NEWER= 512


class SynoArchiveKeytype(IntFlag):
    SYSTEM= 0, # System
    NANO= 1, # Nano
    JSON= 2, # SecurityJson
    SPK= 3, # Spk
    UNK4= 4, # ?
    SSDB= 5, # SECURITYSCAN_DB
    UNK6= 6, # ?
    UNK7= 7, # ?
    DEV= 8, # /var/packages/syno_dev_token
    WEDJAT= 9, # Wedjat
    UNK10= 10, # ?
    SMALL= 11 # Small Patch


class SynoArchiveCtx(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("info", ctypes.c_char_p),
        ("errnum", ctypes.c_uint)
    ]

class SynoArchive(object):
    def __init__(self, dest):
        self.ctx = _synoarchive_init(ctypes.c_char_p(dest.encode("ascii")))

    def open(self, keytype, archive):
        result = _synoarchive_open(
            ctypes.c_void_p(self.ctx),
            ctypes.c_char_p(archive.encode("ascii")),
            keytype
        )

        if not result:
            return SynoArchiveCtx.from_address(self.ctx).errnum
        else:
            return 0

    def extract(self, flags, files=[]):
        if not files:
            result = _synoarchive_extract_multiple(
                ctypes.c_void_p(self.ctx),
                None,
                flags
            )
        else:
            files = [file.encode("ascii") for file in files]
            files.append(None)
            c_files = (ctypes.c_char_p * (len(files)))()
            c_files[:] = files
            result = _synoarchive_extract_multiple(
                ctypes.c_void_p(self.ctx),
                c_files,
                flags
            )

        if not result:
            return SynoArchiveCtx.from_address(self.ctx).errnum
        else:
            return 0

    def info(self):
        ctx_struct = SynoArchiveCtx.from_address(self.ctx)
        return ctypes.c_char_p(ctx_struct.info).value

    def __del__(self):
        _synoarchive_free(self.ctx)


def extractFileFromArchive(keytype: str,archive: str, destdir: str, paths: list = []) -> bool:
    """
    Args:
        keytype (str)
        archive (str): SynoArchive file path.
        destdir (str): The directory to which to extract files.
        paths (list): The paths in DB to extract.
            It will extract all files if this argument is `None` or the list is empty.

    Returns:
        bool: True if successful, False otherwise.
    """

    archiver = SynoArchive(destdir)
    flags = SynoArchiveFlags.OWNER | SynoArchiveFlags.PERM | SynoArchiveFlags.TIME
    _keytype = SynoArchiveKeytype[keytype]

    ret = archiver.open(_keytype, archive)
    if 0 != ret:
        print('Failed to open SynoArchive(errno: {})'.format(ret))
        return False

    ret = archiver.extract(flags, paths)
    if 0 != ret:
        print('Failed to extract file (errno: {})'.format(ret))
        return False

    return True

print("Synology Archive Extractor v0.9 - K4L0")
print("---------------------------------------")
parser = argparse.ArgumentParser(description='example: "sudo python sae.py -k SYSTEM  -a DSM_DS918+_42962.pat -d ."')
parser.add_argument('-k', '--keytype',type=str, required=True, help='SynoArchive keytype.', choices=['SYSTEM', 'NANO', 'JSON', 'SPK', 'UNK4','SSDB','UNK6','UNK7','DEV','WEDJAT','UNK10','SMALL'])
parser.add_argument('-a', '--archive',type=str, required=True, help='SynoArchive file path.')
parser.add_argument('-d', '--destdir',type=str, required=True, help='The directory to which to extract files.')
args = parser.parse_args()

f=extractFileFromArchive(args.keytype, args.archive, args.destdir)
print(f)
