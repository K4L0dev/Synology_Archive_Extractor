# Based on synology source 

import ctypes
from enum import IntFlag
import argparse
import os

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
    SYSTEM= 0, # DSM
    NANO= 1, # NANO
    JSON= 2, # NANO_META
    SPK= 3, # PKG
    SYNOMIBCOLLECTOR= 4, # SYNOMIBCOLLECTOR
    SSDB= 5, # SECURITYSCAN_DB
    AUTOUPDATE= 6, # AUTOUPDATE
    FIRMWARE= 7, # FIRMWARE
    DEV= 8, # PKG_DEV_TOKEN (/var/packages/syno_dev_token)
    WEDJAT= 9, # SYNOPROTECTION (Wedjat)
    DSM_SUPPORT_PATCH= 10, # DSM_SUPPORT_PATCH
    SMALL= 11 # JUNIOR_EXPANSION_PACK_PATCH (Small Patch)

class SynoArchiveErrortype(IntFlag):
    OK = 0,
    ERR_OPEN_ARCHIVE_FAILED = 1,
    ERR_READ_VERSION = 2,
    ERR_READ_HEADER_LEN = 3,
    ERR_READ_HEADER = 4,
    ERR_SODIUM_INIT_FAILED = 5,
    ERR_INVALID_FORMAT = 6,
    ERR_INVALID_VERSION = 7,
    ERR_INVALID_HEADER = 8,
    ERR_INVALID_HEADER_MSGUNPACK = 9,
    ERR_INVALID_HEADER_OBJECT_TYPE = 10,
    ERR_INVALID_HEADER_UUID_TYPE = 11,
    ERR_INVALID_HEADER_UUID_SIZE = 12,
    ERR_CREATE_ENTRY_KEY = 13,
    ERR_INVALID_SIGNATURE = 14,
    ERR_READ_NEW_FAILED = 15,
    ERR_WRITE_DISK_NEW_FAILED = 16,
    ERR_FILEPATH = 17,
    ERR_FILE_NOT_FOUND = 18,
    ERR_HEADER_EXCEED_MAX = 19,
    ERR_UNKNOWN_KEY_TYPE = 20,
    ERR_EXPIRED = 21,
    ERR_SERIALNUM_MISMATCH = 22,
    ERR_OPEN_FILE = 23

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

print("Synology Archive Extractor v0.92 - K4L0")
print("---------------------------------------")
if os.geteuid() != 0:
   print("You are not root permission!") 
   exit
else:
   parser = argparse.ArgumentParser(description='example: "sudo python sae.py -k SYSTEM  -a DSM_DS918+_42962.pat -d ."')
   parser.add_argument('-k', '--keytype',type=str, required=True, help='SynoArchive keytype.', choices=['SYSTEM', 'NANO', 'JSON', 'SPK', 'SYNOMIBCOLLECTOR','SSDB','AUTOUPDATE','FIRMWARE','DEV','WEDJAT','DSM_SUPPORT_PATCH','SMALL'])
   parser.add_argument('-a', '--archive',type=str, required=True, help='SynoArchive file path.')
   parser.add_argument('-d', '--destdir',type=str, required=True, help='The directory to which to extract files.')
   args = parser.parse_args()

   f=extractFileFromArchive(args.keytype, args.archive, args.destdir)
   print(f)
