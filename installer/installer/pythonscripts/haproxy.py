from __future__ import absolute_import, division, print_function, unicode_literals
 
# stdlib
import logging,sys
import socket
from cStringIO import StringIO
from time import time
from traceback import format_exc
 
logger = logging.getLogger(__name__)
 
class HAProxyStats(object):
    """ Used for communicating with HAProxy through its local UNIX socket interface.
    """
    
    
    def __init__(self, socket_name=None):
        self.socket_name = socket_name
 
    def execute(self, command, extra="", timeout=200):
        """ Executes a HAProxy command by sending a message to a HAProxy's local
        UNIX socket and waiting up to 'timeout' milliseconds for the response.
        """
 
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
            logger.error(msg)
            raise
        
        client.close()

    def get_idx(self,field):
        return filter(lambda x: x[1][1] == field, self.HAPROXY_STAT_CSV)[0][0]

 
    
if __name__ == '__main__': 
    stats = HAProxyStats('/home/ubuntu/haproxy.sock')
    if (sys.argv[1] == 'info'):
        info = stats.execute('show info')
        print(info) 
    if (sys.argv[1] == 'stat'):
        stat = stats.execute('show stat')
        print(stat) 
    #sess = stats.execute('show sess', '0x19e8fd0', 20)
    #print(sess)