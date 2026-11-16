import asyncio
import json
import socket
import ssl
import tempfile
import unittest
from pathlib import Path

import httpx
import uvicorn
import websockets
from cryptography import x509
from cryptography.x509.oid import ExtendedKeyUsageOID
from fastapi.testclient import TestClient

from local_tls import certificate_info, prepare_certificates
from server import create_app


class CertificateTests(unittest.TestCase):
    def test_ca_reused_leaf_has_local_sans_and_only_public_cert_is_downloadable(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            first=prepare_certificates({'127.0.0.1','192.168.1.5'},folder)
            second=prepare_certificates({'127.0.0.1','192.168.1.6'},folder)
            self.assertEqual(first['sha256'],second['sha256'])
            cert=x509.load_pem_x509_certificate((folder/'server-cert.pem').read_bytes())
            sans=cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            self.assertIn('localhost',sans.get_values_for_type(x509.DNSName))
            self.assertIn('192.168.1.6',[str(ip) for ip in sans.get_values_for_type(x509.IPAddress)])
            self.assertIn(ExtendedKeyUsageOID.SERVER_AUTH,cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value)
            app=create_app(addresses={'localhost','192.168.1.6'},scheme='https',tls_dir=folder)
            with TestClient(app,base_url='https://localhost:8765',client=('127.0.0.1',1234)) as client:
                self.assertTrue(app.state.room.urls()[0].startswith('https://'))
                public=client.get('/motion-ca.crt');self.assertEqual(public.status_code,200)
                self.assertNotIn(b'PRIVATE KEY',public.content)
                for path in ['/ca-key.pem','/server-key.pem','/static/../ca-key.pem']:
                    self.assertEqual(client.get(path).status_code,404)

    def test_partial_or_corrupt_trust_material_is_not_replaced_silently(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'NONA-local-CA.crt';path.write_text('broken')
            self.assertFalse(certificate_info(folder)['prepared'])
            with self.assertRaises(ValueError):prepare_certificates({'127.0.0.1'},folder)
            self.assertEqual(path.read_text(),'broken')


class SecureTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_https_and_wss_pairing_without_disabling_certificate_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);prepare_certificates({'127.0.0.1'},folder)
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.bind(('127.0.0.1',0));sock.listen(10)
            port=sock.getsockname()[1];origin=f'https://127.0.0.1:{port}'
            app=create_app(port=port,addresses={'127.0.0.1'},scheme='https',tls_dir=folder)
            service=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False,proxy_headers=False,
                ssl_certfile=str(folder/'server-cert.pem'),ssl_keyfile=str(folder/'server-key.pem')))
            task=asyncio.create_task(service.serve(sockets=[sock]))
            try:
                while not service.started:await asyncio.sleep(.01)
                with self.assertRaises(httpx.ConnectError):
                    async with httpx.AsyncClient(trust_env=False) as client:await client.get(origin)
                context=ssl.create_default_context(cafile=str(folder/'NONA-local-CA.crt'))
                async with httpx.AsyncClient(verify=context,trust_env=False) as client:
                    self.assertEqual((await client.get(origin)).status_code,200)
                async with websockets.connect(f'wss://127.0.0.1:{port}/ws/controller?token={app.state.room.token}',
                                               ssl=context,origin=origin,proxy=None) as phone:
                    await phone.send(json.dumps({'seq':0,'buttons':['a'],'steering':.5}))
                    self.assertEqual(json.loads(await phone.recv())['seq'],0)
                    self.assertEqual(app.state.room.steering,.5)
            finally:
                service.should_exit=True;await task;sock.close()
