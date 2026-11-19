from hashlib import sha256

import pytest

from eth_consensus_specs.utils import xmss


def _fake_signature(pubkey, leaf_index, message):
    body = sha256(bytes(pubkey) + bytes(message)).digest()
    leaf = int(leaf_index).to_bytes(xmss.LEAF_INDEX_SIZE, "little")
    return (leaf + body).ljust(xmss.SIGNATURE_SIZE, b"\x00")


@pytest.fixture
def fake_xmss(monkeypatch):
    """
    Stand in for leanXMSS, whose key generation takes minutes, with a scheme
    that binds a signature to the public key, leaf index and message, so
    tests can still tell valid signatures from invalid ones.
    """
    monkeypatch.setattr(xmss, "SkToPk", xmss.StubPk)
    monkeypatch.setattr(
        xmss,
        "Sign",
        lambda SK, leaf_index, message: _fake_signature(xmss.StubPk(SK), leaf_index, message),
    )
    monkeypatch.setattr(
        xmss,
        "Verify",
        lambda PK, leaf_index, message, signature: (
            bytes(signature) == _fake_signature(PK, leaf_index, message)
        ),
    )
