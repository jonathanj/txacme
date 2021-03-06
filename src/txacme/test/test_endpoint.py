"""
Tests for `txacme.endpoint`.
"""
from datetime import datetime

from fixtures import TempDir
from testtools import ExpectedException, TestCase
from testtools.matchers import (
    Equals, Is, IsInstance, MatchesAll, MatchesPredicate, MatchesStructure)
from testtools.twistedsupport import succeeded
from twisted.internet.defer import succeed
from twisted.internet.interfaces import (
    IListeningPort, IStreamServerEndpoint, IStreamServerEndpointStringParser)
from twisted.internet.protocol import Factory
from twisted.internet.task import Clock
from twisted.plugin import IPlugin
from twisted.plugins import txacme_endpoint
from twisted.python.filepath import FilePath
from twisted.python.url import URL
from txsni.snimap import HostDirectoryMap
from zope.interface import implementer
from zope.interface.verify import verifyObject

from txacme.client import LETSENCRYPT_DIRECTORY, LETSENCRYPT_STAGING_DIRECTORY
from txacme.endpoint import _AcmeParser, AutoTLSEndpoint
from txacme.store import DirectoryStore
from txacme.test.test_client import Always, RSA_KEY_512
from txacme.testing import FakeClient, MemoryStore


@implementer(IListeningPort)
class DummyPort(object):
    """
    Port implementation that does nothing.
    """
    def stopListening(self):  # noqa
        pass


@implementer(IStreamServerEndpoint)
class DummyEndpoint(object):
    """
    Endpoint implementation that does nothing.
    """
    def listen(self, factory):
        return succeed(DummyPort())


class EndpointTests(TestCase):
    """
    Tests for `~txacme.endpoint.AutoTLSEndpoint`.
    """
    def setUp(self):
        super(EndpointTests, self).setUp()
        clock = Clock()
        clock.rightNow = (
            datetime.now() - datetime(1970, 1, 1)).total_seconds()
        client = FakeClient(RSA_KEY_512, clock)
        self.endpoint = AutoTLSEndpoint(
            reactor=clock,
            directory=URL(u'https://example.com/'),
            client_creator=lambda reactor, directory: succeed(client),
            cert_store=MemoryStore(),
            cert_mapping={},
            sub_endpoint=DummyEndpoint())

    def test_directory_url_type(self):
        """
        `~txacme.endpoint.AutoTLSEndpoint` expects a ``twisted.python.url.URL``
        instance for the ``directory`` argument.
        """
        with ExpectedException(TypeError):
            AutoTLSEndpoint(
                reactor=Clock(),
                directory='/wrong/kind/of/directory',
                client_creator=None,
                cert_store=None,
                cert_mapping={},
                sub_endpoint=DummyEndpoint())

    def test_listen_starts_service(self):
        """
        ``AutoTLSEndpoint.listen`` starts an ``AcmeIssuingService``.  Stopping
        the port stops the service.
        """
        factory = Factory()
        d = self.endpoint.listen(factory)
        self.assertThat(
            d,
            succeeded(
                MatchesPredicate(
                    IListeningPort.providedBy,
                    '%r does not provide IListeningPort')))
        port = d.result
        self.assertThat(
            self.endpoint.service,
            MatchesStructure(running=Equals(True)))
        self.assertThat(port.stopListening(), succeeded(Always()))
        self.assertThat(
            self.endpoint.service,
            MatchesStructure(running=Equals(False)))


class PluginTests(TestCase):
    """
    Tests for the plugins.
    """
    def test_le_parser(self):
        """
        The ``le:`` parser uses the Let's Encrypt production directory, and
        provides the relevant interfaces.
        """
        verifyObject(
            IPlugin, txacme_endpoint.le_parser)
        verifyObject(
            IStreamServerEndpointStringParser, txacme_endpoint.le_parser)
        self.assertThat(
            txacme_endpoint.le_parser,
            MatchesStructure(
                prefix=Equals('le'),
                directory=Equals(LETSENCRYPT_DIRECTORY)))

    def test_lets_parser(self):
        """
        The ``lets:`` parser uses the Let's Encrypt staging directory, and
        provides the relevant interfaces.
        """
        verifyObject(
            IPlugin, txacme_endpoint.lets_parser)
        verifyObject(
            IStreamServerEndpointStringParser, txacme_endpoint.lets_parser)
        self.assertThat(
            txacme_endpoint.lets_parser,
            MatchesStructure(
                prefix=Equals('lets'),
                directory=Equals(LETSENCRYPT_STAGING_DIRECTORY)))

    def test_parser(self):
        """
        ``AcmeParser`` creates an endpoint with the specified ACME directory
        and directory store.
        """
        directory = URL.fromText(u'https://example.com/acme')
        parser = _AcmeParser(u'prefix', directory)
        tempdir = self.useFixture(TempDir()).path
        temp_path = FilePath(tempdir)
        key_path = temp_path.child('client.key')
        reactor = object()
        self.assertThat(
            parser.parseStreamServer(reactor, tempdir, 'tcp', '443'),
            MatchesAll(
                IsInstance(AutoTLSEndpoint),
                MatchesStructure(
                    reactor=Is(reactor),
                    directory=Equals(directory),
                    cert_store=MatchesAll(
                        IsInstance(DirectoryStore),
                        MatchesStructure(
                            path=Equals(temp_path))),
                    cert_mapping=MatchesAll(
                        IsInstance(HostDirectoryMap),
                        MatchesStructure(
                            directoryPath=Equals(temp_path))),
                    sub_endpoint=MatchesPredicate(
                        IStreamServerEndpoint.providedBy,
                        '%r is not a stream server endpoint'))))
        self.assertThat(key_path.isfile(), Equals(True))
        key_data = key_path.getContent()
        parser.parseStreamServer(reactor, tempdir, 'tcp', '443'),
        self.assertThat(key_path.getContent(), Equals(key_data))


__all__ = ['EndpointTests', 'PluginTests']
