import sys
import hashlib

BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

#Compute hash key from a list of files and a list of dicts
def get_hash(in_memory_files, dicts):
    hashed = hashlib.sha1()
    for file_ in in_memory_files:
        while True:
            data = file_.read(BUF_SIZE)
            if not data:
                break
            hashed.update(data)
    for file_ in in_memory_files:
        file_.seek(0)
    for dict_ in dicts:
        hashed.update(str(dict_).encode('utf-8'))
    return hashed.digest()