"""M-Pesa Security Credentials Generator."""

import base64
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.configuration.settings import settings


def generate_security_credential(
    initiator_password: str | None = None,
    certificate_path: str | Path | None = None,
) -> str:
    """
    Generate a secured and encrypted credential for the Safaricom API using the given
    password and certificate file. The function encrypts the provided initiator password
    using an RSA public key extracted from the given or default certificate path, encoding
    the result in base64 format.

    :param initiator_password: The password of the initiator to be encrypted. If None,
        a default password specified in application settings will be used.
    :type initiator_password: str | None

    :param certificate_path: The file path for the certificate containing the public key
        to be used for encryption. If None, a default certificate path from
        application settings will be used.
    :type certificate_path: str | Path | None

    :return: A base64-encoded encrypted string of the input password using
        the retrieved RSA public key.
    :rtype: str
    """
    password = initiator_password or settings.DARAJA_INITIATOR_PASSWORD
    cert_path = Path(certificate_path or settings.DARAJA_CERTIFICATE_PATH)

    if not cert_path.exists():
        raise FileNotFoundError(f"Certificate not found: {cert_path}")

    # load the certificate and extract the public key
    with open(cert_path, "rb") as f:
        certificate = x509.load_pem_x509_certificate(f.read())
    public_key = certificate.public_key()

    # cast to RSAPublicKey for type checking
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Certificate does not contain an RSA public key")

    # encrypt the password using RSA with PKCS#1 v1.5 padding
    encrypted = public_key.encrypt(password.encode("utf-8"), padding.PKCS1v15())

    return base64.b64encode(encrypted).decode("utf-8")
