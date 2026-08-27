UInt64 = int
ValidatorIndex = UInt64
Slot = UInt64
Height = UInt64
Gwei = UInt64
Round = UInt64
Millis = int
Root = bytes
Signature = bytes
Bitlist = list[bool]

EMPTY_ROOT = Root(b"\x00" * 32)
