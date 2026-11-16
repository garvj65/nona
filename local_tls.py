"""Optional development HTTPS. Certificates stay outside the repository."""
import hashlib
import ipaddress
import os
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path


def tls_folder():
    base = Path(os.environ['LOCALAPPDATA']) / 'NONA' if os.environ.get('LOCALAPPDATA') else Path.home() / '.local' / 'share' / 'nona'
    return base / 'tls'


def certificate_info(folder=None):
    folder = Path(folder) if folder else tls_folder()
    path = folder / 'NONA-local-CA.crt'
    if not path.is_file():
        return {'prepared': False}
    try:
        der = ssl.PEM_cert_to_DER_cert(path.read_text(encoding='ascii'))
    except (OSError, ValueError, ssl.SSLError):
        return {'prepared': False, 'error': 'The local public CA certificate could not be read. Recheck motion setup.'}
    fingerprint = hashlib.sha256(der).hexdigest().upper()
    return {'prepared': True, 'sha256': ':'.join(fingerprint[i:i+2] for i in range(0,len(fingerprint),2))}


def prepare_certificates(addresses, folder=None):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    folder = Path(folder) if folder else tls_folder()
    folder.mkdir(parents=True, exist_ok=True)
    ca_path, ca_key_path = folder / 'NONA-local-CA.crt', folder / 'ca-key.pem'
    now = datetime.now(timezone.utc)
    if ca_path.exists() != ca_key_path.exists():
        raise ValueError('Incomplete local CA files. Back them up and fix them before regenerating trust.')
    if ca_path.exists():
        ca = x509.load_pem_x509_certificate(ca_path.read_bytes())
        ca_key = serialization.load_pem_private_key(ca_key_path.read_bytes(), password=None)
        if ca.public_key().public_numbers() != ca_key.public_key().public_numbers():
            raise ValueError('The existing CA certificate and key do not match.')
        if ca.not_valid_after_utc < now+timedelta(days=2):
            raise ValueError('The local CA is expired or expiring. Remove old trust before creating a new CA.')
    else:
        ca_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'NONA local motion test CA')])
        ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(ca_key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5))
              .not_valid_after(now+timedelta(days=365)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
              .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),critical=False)
              .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),critical=False)
              .add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=False,key_cert_sign=True,
                             crl_sign=True,content_commitment=False,data_encipherment=False,key_agreement=False,
                             encipher_only=False,decipher_only=False),critical=True).sign(ca_key,hashes.SHA256()))
        _write_private(ca_key_path,ca_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    names=[x509.DNSName('localhost')]
    for address in sorted(set(addresses)|{'127.0.0.1'}):
        try:names.append(x509.IPAddress(ipaddress.ip_address(address)))
        except ValueError:pass
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'NONA local controller')])
    expiry=min(now+timedelta(days=90),ca.not_valid_after_utc)
    cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(ca.subject).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(expiry)
          .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
          .add_extension(x509.SubjectAlternativeName(names),critical=False)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()),critical=False)
          .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),critical=False)
          .add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=True,key_cert_sign=False,
                         crl_sign=False,content_commitment=False,data_encipherment=False,key_agreement=False,
                         encipher_only=False,decipher_only=False),critical=True)
          .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False)
          .sign(ca_key,hashes.SHA256()))
    _write_private(folder/'server-key.pem',key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    (folder/'server-cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM)+ca.public_bytes(serialization.Encoding.PEM))
    return certificate_info(folder)


def _write_private(path,content):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'wb') as output:output.write(content)
    if os.name!='nt':path.chmod(0o600)


if __name__=='__main__':
    from server import local_addresses
    info=prepare_certificates(local_addresses())
    print('Local HTTPS certificates prepared. No certificate trust settings were changed.')
    print('Public CA:',tls_folder()/'NONA-local-CA.crt')
    print('CA SHA-256:',info['sha256'])
    print('Read docs/MOTION_TEST.md for Windows and Android trust steps before HTTPS launch.')
