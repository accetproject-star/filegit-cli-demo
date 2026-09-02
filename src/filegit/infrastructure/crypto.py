import nacl.signing
import nacl.encoding
from filegit.domain.ports import CryptoPort
from filegit.domain.errors import SignatureError, KeyError

class PyNaClCrypto(CryptoPort):
    def generate_keypair(self) -> tuple[bytes, bytes]:
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        return (
            signing_key.encode(encoder=nacl.encoding.RawEncoder),
            verify_key.encode(encoder=nacl.encoding.RawEncoder)
        )

    def sign(self, private_key: bytes, message: bytes) -> str:
        try:
            signing_key = nacl.signing.SigningKey(private_key, encoder=nacl.encoding.RawEncoder)
            signed = signing_key.sign(message)
            return nacl.encoding.Base64Encoder.encode(signed.signature).decode('utf-8')
        except Exception as e:
            raise KeyError(f"Failed to sign message: {str(e)}")

    def verify(self, public_key: bytes, message: bytes, signature: str) -> bool:
        try:
            verify_key = nacl.signing.VerifyKey(public_key, encoder=nacl.encoding.RawEncoder)
            sig_bytes = nacl.encoding.Base64Encoder.decode(signature.encode('utf-8'))
            verify_key.verify(message, sig_bytes)
            return True
        except Exception:
            # Catch base64 errors or bad signature errors
            return False
