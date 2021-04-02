#!/usr/bin/env python3
from twisted.internet import protocol, reactor, endpoints
from twisted.protocols import basic

class GalaxyProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        line = line.decode("utf-8")
        print(line)
        self.transport.write(f"Received line: {line}\r\n".encode("utf-8"))
        if line.strip().lower() == "quit":
            self.quit()
    def quit(self):
        self.transport.loseConnection()
class GalaxyFactory(protocol.ServerFactory):
    protocol = GalaxyProtocol
galaxyEndpoint = endpoints.serverFromString(reactor, "tcp:7777")
galaxyEndpoint.listen(GalaxyFactory())
reactor.run()
        

