"""Small dependency-free Ed25519 verifier for Kodi's embedded Python runtime."""

import hashlib

Q = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, Q - 2, Q)) % Q
I = pow(2, (Q - 1) // 4, Q)


def _xrecover(y):
    xx = (y * y - 1) * pow(D * y * y + 1, Q - 2, Q)
    x = pow(xx, (Q + 3) // 8, Q)
    if (x * x - xx) % Q:
        x = (x * I) % Q
    return Q - x if x & 1 else x


B_Y = (4 * pow(5, Q - 2, Q)) % Q
B = (_xrecover(B_Y), B_Y)


def _edwards(p, q):
    x1, y1 = p
    x2, y2 = q
    denominator = D * x1 * x2 * y1 * y2
    x3 = (x1 * y2 + x2 * y1) * pow(1 + denominator, Q - 2, Q)
    y3 = (y1 * y2 + x1 * x2) * pow(1 - denominator, Q - 2, Q)
    return x3 % Q, y3 % Q


def _scalarmult(point, scalar):
    result = (0, 1)
    addend = point
    while scalar:
        if scalar & 1:
            result = _edwards(result, addend)
        addend = _edwards(addend, addend)
        scalar >>= 1
    return result


def _decodepoint(value):
    if len(value) != 32:
        raise ValueError("invalid point length")
    y = int.from_bytes(value, "little") & ((1 << 255) - 1)
    if y >= Q:
        raise ValueError("invalid point")
    x = _xrecover(y)
    if bool(x & 1) != bool(value[31] & 0x80):
        x = Q - x
    point = (x, y)
    if _scalarmult(point, L) != (0, 1):
        raise ValueError("point outside prime subgroup")
    return point


def _encodepoint(point):
    x, y = point
    encoded = bytearray(y.to_bytes(32, "little"))
    encoded[31] |= (x & 1) << 7
    return bytes(encoded)


def verify(signature, message, public_key):
    if len(signature) != 64 or len(public_key) != 32:
        return False
    try:
        point_a = _decodepoint(public_key)
        point_r = _decodepoint(signature[:32])
        scalar_s = int.from_bytes(signature[32:], "little")
        if scalar_s >= L:
            return False
        challenge = int.from_bytes(hashlib.sha512(signature[:32] + public_key + message).digest(), "little") % L
        return _encodepoint(_scalarmult(B, scalar_s)) == _encodepoint(_edwards(point_r, _scalarmult(point_a, challenge)))
    except (ValueError, OverflowError):
        return False

