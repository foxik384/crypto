from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import socket

from .asn1 import ElGamalStruct
from .elgamal import ElGamal

del asn1
del elgamal


def add_padding(value: bytes, pad_size: int = 8):
    if (len(value) % pad_size) != 0:
        to_pad = len(value) % pad_size
        integral_data = value[:(len(value) - to_pad)]
        unpadded_data = value[(len(integral_data)):]

        data_block = unpadded_data + b'\x00' * (8 - len(unpadded_data))

        return integral_data + data_block

    else:
        return value


def del_padding(value: bytes, real_size: int, pad_size: int = 8):
    if len(value) > real_size:
        integral_data = value[:(len(value) - pad_size)]
        padded_data = value[len(integral_data):]

        sub = len(value) - real_size
        data = padded_data[:(8 - sub)]

        return integral_data + data

    else:
        return value


def sym_encrypt_msg(data: bytes) -> (int, bytes):
    key = os.urandom(24)
    triple_des = algorithms.TripleDES(key)
    cipher = Cipher(algorithm=triple_des, mode=modes.CBC(bytes(8)),
                    backend=default_backend())
    encryptor = cipher.encryptor()

    b_data_len = (len(data) + 4).to_bytes(4, byteorder='big')
    data = b_data_len + data
    padded_data = add_padding(data)

    ciph_data = encryptor.update(padded_data)
    i_key = int.from_bytes(key, byteorder='big')
    return i_key, ciph_data


def sym_decrypt_msg(i_key: int, ciph_data: bytes) -> bytes:
    key = i_key.to_bytes(24, byteorder='big')
    triple_des = algorithms.TripleDES(key)
    cipher = Cipher(algorithm=triple_des, mode=modes.CBC(bytes(8)),
                    backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(ciph_data)
    data_len = int.from_bytes(padded_data[:4], byteorder='big')

    if (data_len - 4) > len(padded_data):
        print("Message is corrupted")
        return b''

    data = del_padding(padded_data, data_len)[4:]
    return data


def recvall(sock: socket.socket, n: int):
    """ Helper function to recv n bytes or return None if EOF is hit """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data