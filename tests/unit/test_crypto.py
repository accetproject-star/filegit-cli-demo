from filegit.infrastructure.crypto import PyNaClCrypto
from filegit.domain.errors import SignatureError, KeyError
import pytest

def test_generate_keypair():
    crypto = PyNaClCrypto()
    priv, pub = crypto.generate_keypair()
    assert isinstance(priv, bytes)
    assert isinstance(pub, bytes)
    assert len(priv) == 32
    assert len(pub) == 32

def test_sign_and_verify():
    crypto = PyNaClCrypto()
    priv, pub = crypto.generate_keypair()
    
    msg = b"hello world"
    sig = crypto.sign(priv, msg)
    
    assert isinstance(sig, str)
    assert crypto.verify(pub, msg, sig) is True

def test_verify_fails_on_tampered_message():
    crypto = PyNaClCrypto()
    priv, pub = crypto.generate_keypair()
    
    msg = b"hello world"
    sig = crypto.sign(priv, msg)
    
    tampered_msg = b"hello worlds"
    assert crypto.verify(pub, tampered_msg, sig) is False

def test_verify_fails_on_bad_signature():
    crypto = PyNaClCrypto()
    priv, pub = crypto.generate_keypair()
    
    msg = b"hello world"
    assert crypto.verify(pub, msg, "invalidbase58") is False
