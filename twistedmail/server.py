import StringIO
import sys

from OpenSSL.SSL import TLSv1_METHOD

from arangodb.api import Client
from arangodb.models import CollectionModel

from twisted.python import log
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor


class Mailer(object):

    def __init__(self, smtp_host, smtp_port=25, authentication=False, user='', password=''):

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_authentication = authentication
        self.user = user
        self.password = password

    def send(self, from_address, to_address, mail):

        result = self.send_mail(from_address, to_address, message=mail.get_mail())
        result.addCallbacks(self.on_message_sent, self.on_send_error)
        reactor.run()

    def send_mail(self,
        from_address, to_address,
        message
        ):
        # Create a context factory which only allows SSLv3 and does not verify
        # the peer's certificate.
        context_factory = ClientContextFactory()
        context_factory.method = TLSv1_METHOD

        resultDeferred = Deferred()

        senderFactory = ESMTPSenderFactory(
            self.user,
            self.password,
            from_address,
            to_address,
            message,
            resultDeferred,
            contextFactory=context_factory,
            requireAuthentication=self.use_authentication)

        reactor.connectTCP(self.smtp_host, self.smtp_port, senderFactory)

        return resultDeferred

    def on_message_sent(self, result):
        """
        Called when the message has been sent.

        Report success to the user and then stop the reactor.
        """
        print "Message sent"
        reactor.stop()

    def on_send_error(self, err):
        """
        Called if the message cannot be sent.

        Report the failure to the user and then stop the reactor.
        """
        err.printTraceback()
        reactor.stop()


class Mail(CollectionModel):

    collection_name = 'twisted_mail'

    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

    def get_mail(self):
        mail_buffer = 'Subject: %s\r\n%s' % (self.subject, self.message)
        return StringIO.StringIO(mail_buffer)

    # result.addCallbacks(cbSentMessage, ebSentMessage)
    # reactor.run()


log.startLogging(sys.stdout)

Client('localhost')
Mail.init()