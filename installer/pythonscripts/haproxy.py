from __future__ import absolute_import, division, print_function, unicode_literals
 
# stdlib
import logging,sys
import socket
from cStringIO import StringIO
from time import time
from traceback import format_exc
 
class HAProxyStats(object):
    """ Used for communicating with HAProxy through its local UNIX socket interface.    """
    
    
    def __init__(self, socket_name=None):
        self.socket_name = socket_name
        logging.basicConfig(filename='/root/logs/python.log',level=logging.DEBUG)
 
    def execute(self, command, extra="", timeout=200):
        """ Executes a HAProxy command by sending a message to a HAProxy's local
        UNIX socket and waiting up to 'timeout' milliseconds for the response.
        """
        logging.info("inside HAProxyStats:Execute method")
        if extra:
            command = command + ' ' + extra
 
        buff = StringIO()
        end = time() + timeout
 
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
 
        try:
            client.connect(self.socket_name)
            client.send(command + '\n')
 
            while time() <=  end:
                data = client.recv(4096)
                if data:
                    buff.write(data)
                else:
                    return buff.getvalue()
        except Exception, e:
            msg = 'An error has occurred, e=[{e}]'.format(e=format_exc(e))
            logging.error("error in haxproxystat:execute method : %s", msg)          
        
        client.close()

    def get_idx(self,field):
        return filter(lambda x: x[1][1] == field, self.HAPROXY_STAT_CSV)[0][0]

 
    
if __name__ == '__main__': 
    stats = HAProxyStats('/root/haproxy.sock')
    if (sys.argv[1] == 'info'):
        info = stats.execute('show info')
        print(info) 
    if (sys.argv[1] == 'stat'):
        stat = stats.execute('show stat')
        print(stat) 
    