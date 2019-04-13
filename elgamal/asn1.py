from pyasn1.type import univ, char, namedtype

from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder
# All documentation from http://snmplabs.com/


""" ASN.1 structure description """


class _Payload(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("payload_id", univ.OctetString()),
        namedtype.NamedType("file_len", univ.Integer())
    )


class _Ciphertext(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("a_k", univ.Integer()),
        namedtype.NamedType("c", univ.Integer())
    )


class _Parameters(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("prime", univ.Integer()),
        namedtype.NamedType("generator", univ.Integer())
    )


class _PublicKey(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("y", univ.Integer())
    )


class _FirstKey(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("algorithm_id", univ.OctetString()),
        namedtype.NamedType("str_key_id", char.UTF8String()),
        namedtype.NamedType("public_key", _PublicKey()),
        namedtype.NamedType("parameters", _Parameters()),
        namedtype.NamedType("ciphertext", _Ciphertext())
    )


class _Keys(univ.Set):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("first_key", _FirstKey())
    )


class _Header(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('keys', _Keys()),
        namedtype.NamedType('payload', _Payload()),
    )


""" Main functions """


def encode(a_k: int, c: int, p: int, g: int, y: int, encrypted_msg: bytes,
           msg_len: int = 0) -> bytes:
    private = _Header()
    private["keys"]["first_key"]["algorithm_id"] = b"\x80\x01\x02\x03"
    private["keys"]["first_key"]["str_key_id"] = "test"
    private["keys"]["first_key"]["public_key"]["y"] = y
    private["keys"]["first_key"]["parameters"]["prime"] = p
    private["keys"]["first_key"]["parameters"]["generator"] = g
    private["keys"]["first_key"]["ciphertext"]["a_k"] = a_k
    private["keys"]["first_key"]["ciphertext"]["c"] = c
    private["payload"]["payload_id"] = 0x0132.to_bytes(2, byteorder="big")

    if msg_len == 0:
        private["payload"]["file_len"] = len(encrypted_msg)
    else:
        private["payload"]["file_len"] = 0

    encoded_header = der_encoder(private)
    return encoded_header + encrypted_msg


def decode(encoded_msg: bytes) -> (int, int, int, bytes, int):
    """Returns (a_k, c, p, g, y)"""
    private, encrypted_msg = der_decoder(encoded_msg, asn1Spec=_Header())

    y = private["keys"]["first_key"]["public_key"]["y"]
    p = private["keys"]["first_key"]["parameters"]["prime"]
    g = private["keys"]["first_key"]["parameters"]["generator"]
    a_k = private["keys"]["first_key"]["ciphertext"]["a_k"]
    c = private["keys"]["first_key"]["ciphertext"]["c"]

    msg_len = int(private["payload"]["file_len"])
    return a_k, c, p, g, y, encrypted_msg, msg_len