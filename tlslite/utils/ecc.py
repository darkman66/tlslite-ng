# Copyright (c) 2015, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.
"""Methods for dealing with ECC points"""
import logging
from .codec import Parser, Writer, DecodeError
from .cryptomath import bytesToNumber, numberToByteArray, numBytes
from .compat import ecdsaAllCurves
import ecdsa


old_init = ecdsa.ellipticcurve.Point.__init__


def new_init(self, curve, x, y, order=None):
    try:
        old_init(self, curve, x, y, order)
    except AssertionError:
        if curve and curve.cofactor() != 1 and order:
            assert self * order == INFINITY


# class MyPoint(ecdsa.ellipticcurve.Point):

#     def __init__(self, curve, x, y, order=None):
#         """curve, x, y, order; order (optional) is the order of this point."""
#         try:
#             super().__init__(curve, x, y, order)
#         except AssertionError:
#             if curve and curve.cofactor() != 1 and order:
#                 assert self * order == ecdsa.ellipticcurve.INFINITY

ecdsa.ellipticcurve.Point.__init__ = new_init


def decodeX962Point(data, curve=ecdsa.NIST256p):
    """Decode a point from a X9.62 encoding"""
    parser = Parser(data)
    encFormat = parser.get(1)
    if encFormat != 4:
        raise DecodeError("Not an uncompressed point encoding")
    bytelength = getPointByteSize(curve)
    x_bytes = parser.getFixBytes(bytelength)
    xCoord = bytesToNumber(x_bytes)
    y_bytes = parser.getFixBytes(bytelength)
    yCoord = bytesToNumber(y_bytes)
    logging.debug(f"x bytes: {x_bytes.hex()}")
    logging.debug(f"y bytes: {y_bytes.hex()}")
    logging.debug(f"data: {data.hex()}")
    logging.debug(f"bytelength: {bytelength}")
    logging.debug(f"xCoord: {xCoord}")
    logging.debug(f"yCoord: {yCoord}")
    if parser.getRemainingLength():
        raise DecodeError("Invalid length of point encoding for curve")
    return ecdsa.ellipticcurve.Point(curve.curve, xCoord, yCoord)


def encodeX962Point(point):
    """Encode a point in X9.62 format"""
    bytelength = numBytes(point.curve().p())
    writer = Writer()
    writer.add(4, 1)
    writer.bytes += numberToByteArray(point.x(), bytelength)
    writer.bytes += numberToByteArray(point.y(), bytelength)
    return writer.bytes


def getCurveByName(curveName):
    """Return curve identified by curveName"""
    curveMap = {
        "secp256r1": ecdsa.NIST256p,
        "secp384r1": ecdsa.NIST384p,
        "secp521r1": ecdsa.NIST521p,
        "secp256k1": ecdsa.SECP256k1,
        "brainpoolP256r1": ecdsa.BRAINPOOLP256r1,
        "brainpoolP384r1": ecdsa.BRAINPOOLP384r1,
        "brainpoolP512r1": ecdsa.BRAINPOOLP512r1,
    }
    if ecdsaAllCurves:
        curveMap["secp224r1"] = ecdsa.NIST224p
        curveMap["secp192r1"] = ecdsa.NIST192p

    if curveName in curveMap:
        return curveMap[curveName]
    else:
        raise ValueError("Curve of name '{0}' unknown".format(curveName))


def getPointByteSize(point):
    """Convert the point or curve bit size to bytes"""
    curveMap = {
        ecdsa.NIST256p.curve: 256 // 8,
        ecdsa.NIST384p.curve: 384 // 8,
        ecdsa.NIST521p.curve: (521 + 7) // 8,
        ecdsa.SECP256k1.curve: 256 // 8,
        ecdsa.BRAINPOOLP256r1.curve: 256 // 8,
        ecdsa.BRAINPOOLP384r1.curve: 384 // 8,
        ecdsa.BRAINPOOLP512r1.curve: 512 // 8,
    }
    if ecdsaAllCurves:
        curveMap[ecdsa.NIST224p.curve] = 224 // 8
        curveMap[ecdsa.NIST192p.curve] = 192 // 8

    if hasattr(point, "curve"):
        if callable(point.curve):
            return curveMap[point.curve()]
        else:
            return curveMap[point.curve]
    if point is None:
        return curveMap[ecdsa.NIST256p.curve]
    raise ValueError("Parameter must be a curve or point on curve")
