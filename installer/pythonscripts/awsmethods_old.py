from boto.ec2.connection import EC2Connection
import os
import sys
import pickle
import time
import re
import paramiko
import sys
import logging
import dblayer
from datetime import datetime
from datetime import timedelta
import random
class AWS():
    upscalethreshold = 300
    downscaletime = 2 #minutes
    keyfile = '/home/ubuntu/installer/pythonscripts/ag2.pem'    
    SSH_OPTS      = '-o StrictHostKeyChecking=no -i /home/ubuntu/installer/pythonscripts/ag2.pem'
    prefix = "/home/ubuntu/"
    COPY_DIRS     = ['/home/ubuntu/installer', '/home/ubuntu/userfiles']
    instancesize = {0:"m1.small",1:"m1.large", 2:"m1.xlarge"}
    iscripts = {"php":"shellscripts/installPhp", "mysql":"shellscripts/installMySql_Server", "lb":"shellscripts/installHaProxy","basic":"../shellscripts/prepareinstance.sh"}
    processmap ={"mysql":"","php":"","haproxy":""}
    filesdir = 'installer'
    scriptsdir = 'scripts'
    haproxysockpath = '/home/ubuntu/haproxy.sock'   
    HAPROXY_STAT_MAX_SERVICES = 100
    HAPROXY_STAT_COMMENT = '#'
    HAPROXY_STAT_SEP = ','    
    HAPROXY_STAT_CSV = [
        # Note: Fields mustc be listed in correct order, as described in:
        # http://haproxy.1wt.eu/download/1.4/doc/configuration.txt [9.1]        
        # TYPE  FIELD        
        (str,   'pxname'),          # proxy name
        (str,   'svname'),          # service name (FRONTEND / BACKEND / name)
        (int,   'qcur'),            # current queued requests
        (int,   'qmax'),            # max queued requests
        (int,   'scur'),            # current sessions
        (int,   'smax'),            # max sessions
        (int,   'slim'),            # sessions limit
        (int,   'stot'),            # total sessions
        (int,   'bin'),             # bytes in
        (int,   'bout'),            # bytes out
        (int,   'dreq'),            # denied requests
        (int,   'dresp'),           # denied responses
        (int,   'ereq'),            # request errors
        (int,   'econ'),            # connection errors
        (int,   'eresp'),           # response errors (among which srv_abrt)
        (int,   'wretr'),           # retries (warning)
        (int,   'wredis'),          # redispatches (warning)
        (str,   'status'),          # status (UP/DOWN/NOLB/MAINT/MAINT(via)...)
        (int,   'weight'),          # server weight (server), total weight (backend)
        (int,   'act'),             # server is active (server),
                                    # number of active servers (backend)
        (int,   'bck'),             # server is backup (server),
                                    # number of backup servers (backend)
        (int,   'chkfail'),         # number of failed checks
        (int,   'chkdown'),         # number of UP->DOWN transitions
        (int,   'lastchg'),         # last status change (in seconds)
        (int,   'downtime'),        # total downtime (in seconds)
        (int,   'qlimit'),          # queue limit
        (int,   'pid'),             # process id
        (int,   'iid'),             # unique proxy id
        (int,   'sid'),             # service id (unique inside a proxy)
        (int,   'throttle'),        # warm up status
        (int,   'lbtot'),           # total number of times a server was selected
        (str,   'tracked'),         # id of proxy/server if tracking is enabled
        (int,   'type'),            # (0=frontend, 1=backend, 2=server, 3=socket)
        (int,   'rate'),            # number of sessions per second
                                    # over the last elapsed second
        (int,   'rate_lim'),        # limit on new sessions per second
        (int,   'rate_max'),        # max number of new sessions per second
        (str,   'check_status'),    # status of last health check
        (int,   'check_code'),      # layer5-7 code, if available
        (int,   'check_duration'),  # time in ms took to finish last health check
        (int,   'hrsp_1xx'),        # http responses with 1xx code
        (int,   'hrsp_2xx'),        # http responses with 2xx code
        (int,   'hrsp_3xx'),        # http responses with 3xx code
        (int,   'hrsp_4xx'),        # http responses with 4xx code
        (int,   'hrsp_5xx'),        # http responses with 5xx code
        (int,   'hrsp_other'),      # http responses with other codes (protocol error)
        (str,   'hanafail'),        # failed health checks details
        (int,   'req_rate'),        # HTTP requests per second
        (int,   'req_rate_max'),    # max number of HTTP requests per second
        (int,   'req_tot'),         # total number of HTTP requests received
        (int,   'cli_abrt'),        # number of data transfers aborted by client
        (int,   'srv_abrt'),        # number of data transfers aborted by server
        ]
    
    HAPROXY_STAT_NUMFIELDS = len(HAPROXY_STAT_CSV)
    HAPROXY_STAT_CSV = [(k, v) for k, v in enumerate(HAPROXY_STAT_CSV)]   
    
    
    
    HAPROXY_INFO_RE = {
    'software_name':    re.compile('^Name:\s*(?P<value>\S+)'),
    'software_version': re.compile('^Version:\s*(?P<value>\S+)'),
    'software_release': re.compile('^Release_date:\s*(?P<value>\S+)'),
    'nproc':            re.compile('^Nbproc:\s*(?P<value>\d+)'),
    'procn':            re.compile('^Process_num:\s*(?P<value>\d+)'),
    'pid':              re.compile('^Pid:\s*(?P<value>\d+)'),
    'uptime':           re.compile('^Uptime:\s*(?P<value>[\S ]+)$'),
    'maxconn':          re.compile('^Maxconn:\s*(?P<value>\d+)'),
    'curconn':          re.compile('^CurrConns:\s*(?P<value>\d+)'),
    'maxpipes':         re.compile('^Maxpipes:\s*(?P<value>\d+)'),
    'curpipes':         re.compile('^PipesUsed:\s*(?P<value>\d+)'),
    'tasks':            re.compile('^Tasks:\s*(?P<value>\d+)'),
    'runqueue':         re.compile('^Run_queue:\s*(?P<value>\d+)'),
    'node':             re.compile('^node:\s*(?P<value>\S+)'),
    }
    
    db = None
    timer = None    
    
    def __init__(self):
        try:           
            self.db = dblayer.dblayer()           
        except Exception,e:
            logging.error(str(e))       
         
    def connect(self,accesskey, secretkey):
        '''
            Method to establish connection to EC2.
        '''
        try:
            self.conn = EC2Connection(accesskey, secretkey)            
        except Exception,e:
            logging.error(str(e))  
        return self.conn
    
    def createInstance(self,conn,size,name,type):
        logging.info("Creating instance of type %s size %s and name %s " % (type, str(size), name))
        #IMAGE = 'ami-19e12d70'           
        #IMAGE           = 'ami-89be73e0' # Basic 64-bit Amazon Linux AMI
        IMAGE           = 'ami-fd4aa494' # Basic 64-bit Amazon Linux AMI
        KEY_NAME        = 'ag2key'
        INSTANCE_TYPE   = self.instancesize[size]
        #INSTANCE_TYPE   = 't1.micro'
        ZONE            = 'us-east-1a' # Availability zone must match the volume's
        SECURITY_GROUPS = ['dj'] # Security group allows SSH        
        # Create the EC2 instance
        logging.debug('Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE))        
        reservation = conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, placement=ZONE, security_groups=SECURITY_GROUPS)
        instance = reservation.instances[0]
        time.sleep(20) # Sleep so Amazon recognizes the new instance
        while not instance.update() == 'running':
            time.sleep(5) # Let the instance start up               
        # hack to repopulate the instance object as IP Address doesn't get populated in the first run
        dnsname = instance.dns_name
        
        if(instance.dns_name == None):
            logging.error("Amazon returned the DNS of newly created instance as None. Halting.")
            sys.exit(1)
        
                
        if(dnsname):                   
            if (self.isinstanceready(conn, dnsname)):
                instance = self.getinstance(conn, dnsname)
            else:
                logging.error("Cannot find the instance. System Cannot Proceed Ahead. Halting.")             
                sys.exit(1)
        else:
            logging.error("Instance returned as None by BOTO.")             
            sys.exit(1)
        dnsname = instance.dns_name
        privateip =  instance.private_ip_address                
        logging.debug('Started the instance: {0} having IP Address : {1}'.format(dnsname, privateip))      
        if(type== "mysql"):            
            os.system("echo {1}={0}  >> /home/ubuntu/installer/shellscripts/instances.dat".format(str(privateip),type))
            self.db.createdbinstance(name, dnsname, privateip, type)
        else:
            os.system("echo {0} {1} {2}  >> /home/ubuntu/installer/shellscripts/instances.dat".format(dnsname, str(privateip), type))
            self.db.createdbinstance(name, dnsname, privateip, type)            
        logging.debug("Check if  SSH port is open.")
        
        if(self.issshportopen(dnsname)):           
            logging.debug("Copying Files ")                    
            #copy files to new instance
            for copy_dir in self.COPY_DIRS:
                logging.debug("Copying Dir : %s " % (copy_dir))
                command = "rsync -e \"ssh {0}\" -avz --delete {2} ubuntu@{1}:{3}/ > /home/ubuntu/logs/rsynclogfile 2>&1".format(self.SSH_OPTS, dnsname, copy_dir,"/home/ubuntu/")
                logging.debug("Command Executed : %s" % (command))           
                os.system(command)                   
            #basic preparation
            #logging.debug("Preparing Instance") 
            #logging.debug("Calling Preparing Instance Script File") 
            #self.execute(conn, instance, "/home/ubuntu/installer/shellscripts/prepareinstance.sh")        
            #check type
            logging.debug("Calling Script File to install %s " % type)        
            self.execute(conn, instance, "/home/ubuntu/installer/"+self.iscripts[type])
            logging.info("Instance created and ready for use")
            return instance
        else:
            logging.error("SSH Connection to the host cannot be established. ")
            sys.exit(1)
        
    def prepareinstance(self, type):
        """        
        This method will be used to install all the required softwares and also to copy the required scripts from
        local machine to the remote machine
        """
        if (type == "basic"):
            # this block would be the first block to be called for installing all the basic requirements of the system
            # 1. create a directory for the scripts
            # 2. execute the scripts
            command = "mkdir {0}".format(self.filesdir)
            print "Executing command : ".format(command)
            self.execute(conn, instance, command)
            print "Executed command successfully"   
            # 2. copy the files from local to remote machines
            for copy_dir in self.COPY_DIRS:
                os.system(command)
            print 'File Copy completed.'           
            # execute the scripts
    
    def isinstanceready(self,conn,address):
        logging.info("Inside is instance ready Method")
        instance = self.getinstance(conn, address)
        if(instance):
            return True
        retrycount = 5        
        while(retrycount):
            logging.debug("Unable to fetch instance object. Retry will be attempted after 5 seconds.")            
            time.sleep(5)
            instance = self.getinstance(conn, address)
            if(instance):
                return True
            retrycount = retrycount - 1
        return False
    
            
     
    def issshportopen(self,address):
        logging.info("Inside is SSH Port Open Method for Address : %s " % address)
        retrycount = 3
        while(retrycount):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(address, username="ubuntu", key_filename=self.keyfile)
                logging.debug("SSH Connection Successful")
                return True
            except paramiko.ChannelException,connectionfailed:
                logging.error("Connection Cannot be Established %s" % str(connectionfailed))
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount))    
                time.sleep(retrycount*5)
            except paramiko.AUTH_FAILED,authfailed:
                logging.error("Authentication Error : %s" % str(authfailed))
                retrycount = retrycount - 1
                logging.info("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount)) 
                time.sleep(retrycount*5)
            except Exception,e:
                logging.error("Connection timed out to the client. Retry will be attempted.")
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount))    
                time.sleep(retrycount*5)                        
            finally:
                ssh.close()               
        logging.error("Number of retry Attempt Exceeded.  Task cannot be completed.")
        return False            
    
     
    def deploy(self,conn,instance,target,type):
        #time.sleep(15)        
        deploymentpath = self.filesdir +"/"+self.scriptsdir        
        self.execute(conn, instance, 'sudo {0}/{1}'.format(deploymentpath,self.iscripts[type]))        
        if(type == "php"):
            self.execute(conn, instance, 'sudo cp ./anand3/copyfiles/index.php /var/www')
            command = r"curl http://{0}/{1}".format(instance.dns_name,'index.php')
            print command
            os.system(command)            
            
                
    def getimagelist(self,type):
        images=[]
        if(type == 'all'):
            images = self.conn.get_all_images()
            for image in images:
                image.append(image)
        return images
    
    
    def getallinstance(self,conn):
        reservations=conn.get_all_instances()
        for reservation in reservations:      
            for instant in reservation.instances:                             
                print "State : ",instant.state
                print "DNS_Name : ",instant.dns_name
                print "Architecture : ",instant.architecture
                print "ImageID : ", instant.image_id
                print "KeyName : ", instant.key_name
                print "**********************************************"
                print "IP Address : ", instant.private_ip_address
    
                
    def getinstance(self,conn,dns):
        dns=dns.strip()
        reservations=conn.get_all_instances()
        for reservation in reservations:      
            for instance in reservation.instances:
                if(instance.dns_name == dns):
                    return instance
        return None
    
    def stopinstance(self,conn, dns):
        logging.info("Inside stopinstance method : " + dns)
        instance = self.getinstance(conn, dns)       
        if(instance): 
            instance.stop()
            logging.info("Instance stopped")
            return True
        else:
            logging.info("Invalid instance specified.")
            return False
        
        
    def execute(self, conn, instance, path):
        logging.info("Execution Command: {0} on instance {1} ".format(path, instance))        
        #command = "ssh -t {0} ubuntu@{1} \"{2}\"".format(self.SSH_OPTS, instance.dns_name, path)        
        # http://www.python-forum.org/pythonforum/viewtopic.php?f=5&t=23820
        # nohup your_script.sh > /dev/null 2>&1 &
        command = "nohup bash -c \"%s\" > /dev/null 2>&1 &" % (str(path))
        logging.debug("Command to be Executed ", str(command))        
        retrycount = 3        
        if (instance == None or instance.private_ip_address == None or  len(instance.private_ip_address) < 1):
            logging.debug("Error : Invalid Instance Object")
            
        while(retrycount):
            try:                
                logging.debug("trying to setup SSH Connection")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(instance.dns_name, username="ubuntu", key_filename=self.keyfile)
                logging.debug("SSH Connection Successful")
                logging.debug("Executing Command :", str(command))
                stdin, stdout, stderr = ssh.exec_command(command)                
                data =  stdout.readlines()                
                logging.debug("Execution result : " + str(data))
                return data            
            except paramiko.ChannelException,connectionfailed:
                logging.error("Connection Cannot be Established %s" % str(connectionfailed))
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount))    
                time.sleep(retrycount*5)
            except paramiko.AUTH_FAILED,authfailed:
                logging.error("Authentication Error : %s" % str(authfailed))
                retrycount = retrycount - 1
                logging.info("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount)) 
                time.sleep(retrycount*5)
            except Exception,e:
                logging.error("Exception : %s " % e)
                if(e.errno == 110):
                    logging.error("Connection timed out to the client. Retry will be attempted.")
                    retrycount = retrycount - 1            
                    logging.debug("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount))    
                    time.sleep(retrycount*5)
                if(e.errno == 111):
                    logging.error("Connection Refused. Retry will be attempted.")
                    retrycount = retrycount - 1            
                    logging.debug("Retrying to establish connection.  Attempt Number :  %s" % (3-retrycount))    
                    time.sleep(retrycount*5)        
                else:
                    logging.error("Unknown Exception has occured. System will halt.")
                    sys.exit(1)            
            finally:
                ssh.close()               
        logging.error("Number of retry Attempt Exceeded.  Task cannot be completed.")
        sys.exit(1)            
    
        
    def taginstance(self, instance, tags):
        for tag in tags.keys():
            #instance.add_tag(tag,tags[tag])
            pass
    
    def monitor(self, conn, dns,type):
        '''
        Mehtod to monitor instances for load
        '''
        logging.info("Inside Monitor method at : " + time.ctime())
        logging.debug("Fetching instance object having dns = " + dns)
        instance = AWS().getinstance(conn, dns)
        if(instance == None):
            logging.error("Instance doesn't exsist. Monitoring will be halted.")
            sys.exit(1)
        cmd = "echo \"show stat\" | sudo socat unix-connect:{0}".format(self.haproxysockpath)
        cmd = "sudo python /home/ubuntu/installer/pythonscripts/haproxy.py {0}".format(type)
        try:        
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logging.debug("Trying to connect to EC2 instance")
            ssh.connect(dns, username="ubuntu", key_filename=self.keyfile)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            logging.debug("Successfully connected to EC2 instance")
            logging.debug("Fetching stats for instance")
            data =  stdout.readlines()       
            for line in data:
                # the following length check has been placed to skip un-relevant stats entry
                if(len(line) > 5):
                    splittedline = line.split(',')
                    if splittedline:    
                        if splittedline[0] ==  'web-farm' and splittedline[1] ==  'BACKEND':                        
                            logging.debug("Number of Queued Request : " + str(splittedline[2]))
                            queuelen = int(splittedline[2])
                            logging.debug("Max Queued Request " + str(splittedline[3]))                        
                            #block to decide upscaling                            
                            if( queuelen > self.upscalethreshold):
                                #insert code for creation of new instance                            
                                # create new instance                   
                                logging.debug("Upscale Criteria Satisfied.")         
                                emailid = self.db.getemailbydns(dns)
                                logging.info("Email id fetched : " + str(emailid))
                                logging.info("Triggering Upscale: New instance of type PHP will be created.")
                                self.createInstance(conn, 1, emailid.strip(), "php")
                                # notify haproxy and restart it
                                logging.info("Notifying HaProxy.")
                                self.execute(conn, instance, "/home/ubuntu/installer/"+self.iscripts["lb"])                                                       
                                logging.info("New instance created and updated on LB")
                                self.timer = datetime.now() #reset timer
                            
                            if(queuelen  == 0):
                                logging.debug("Number of queued request is 0")                            
                                # condition for down scaling
                                if(self.timer == None):
                                    logging.debug("Timer started")                            
                                    self.timer = datetime.now()
                                else:
                                    check = datetime.now() - timedelta(minutes = self.downscaletime) > self.timer
                                    logging.debug("Down Scale Check : " + str(check))
                                    if (datetime.now() - timedelta(minutes = self.downscaletime) > self.timer):
                                        emailid = self.db.getemailbydns(dns)
                                        phpinstancecount = self.db.getinstancecount(emailid, "php")
                                        logging.debug("Numer of PHP instances = " + str(phpinstancecount))
                                        if(phpinstancecount > 2):                                        
                                            logging.debug("Down Scale should be triggered")
                                            #pick the instance to be killed
                                            instancetobekilled = random.randint(1,phpinstancecount-1)
                                            logging.debug("Kill the instance : " + str(instancetobekilled))
                                            phpinstancesdnslist = self.db.getinstancesbytype(emailid, "php")
                                            targetinstancedns = phpinstancesdnslist[instancetobekilled]
                                            logging.info("Instance to be killed has DNS  : " + targetinstancedns)                                        
                                            self.stopinstance(conn, targetinstancedns)
                                            # remove the entry from instances.dat
                                            commandtoremoveentry = "sudo grep -v %s /home/ubuntu/installer/shellscripts/instances.dat > temp" % (targetinstancedns)
                                            logging.info("Command to remove entry from Instances.dat : " + commandtoremoveentry) 
                                            os.system(commandtoremoveentry)
                                            os.system("mv temp /home/ubuntu/installer/shellscripts/instances.dat")
                                            # drop entry from table
                                            res = self.db.deleteinstancebydns(targetinstancedns)
                                            #inform haproxy                                                                    
                                            logging.debug("Inform HaProxy about instance termination.")
                                            logging.debug("Calling Script File to install Haproxy")        
                                            self.execute(conn, instance, "/home/ubuntu/installer/"+self.iscripts["lb"])
                                            logging.info("Instance created and ready for use")
                                            logging.debug("Sleeping for 10 seconds")
                                            time.sleep(10)
                                            #reset timer
                                            self.timer = datetime.now()
                                            continue       
                                        
                            
                            if( queuelen < 900 and queuelen >0):
                                logging.debug("Counter will be reset")
                                self.timer = datetime.now()
    
                                
                            #block to decide downscaling                        
                    else:
                        logging.error("Stats couldn't be parsed.")                       
                    #print line        
            #todo: decide if the connection should be setup when the monitor method is invoked or it should be done on every monitor call
        except Exception,ex:
                logging.error("Exception in Monitor method : Details " + str(ex))
        ssh.close()
    
    
    def downscale(self,instance):
        '''
        Method to trigger downscaling of instances        
        '''        
        
        pass
            
    def parse_info(self,iterable):
        '''
        Method picked from HATOP
        __author__    = 'John Feuerstein <john@feurix.com>'
        __copyright__ = 'Copyright (C) 2010 %s' % __author__
        __license__   = 'GNU GPLv3'
        __version__   = '0.7.7'
        '''
        info = {}
        for line in iterable:
            line = line.strip()
            if not line:
                continue
            for key, regexp in self.HAPROXY_INFO_RE.iteritems():
                match = regexp.match(line)
                if match:
                    info[key] = match.group('value')
                    break    
        for key in self.HAPROXY_INFO_RE.iterkeys():
            if not key in info:
                raise RuntimeError('missing "%s" in info data' % key)    
        return info
    
    def get_idx(self,field):
        return filter(lambda x: x[1][1] == field, self.HAPROXY_STAT_CSV)[0][0]
    
    def isprocessactive(self,conn,instance,processname):
        ''' 
            This method will be used if a process is active at remote locatiion.
        '''
        
        command = "ps aux | grep %s | grep -v grep | awk '{print $2}'" % (processname)
        result = self.execute(conn, instance, command)
        if(result):
            return True
        else:
            return False
        
    
    def parse_stat(self,iterable):
        '''
        Method picked from HATOP
        __author__    = 'John Feuerstein <john@feurix.com>'
        __copyright__ = 'Copyright (C) 2010 %s' % __author__
        __license__   = 'GNU GPLv3'
        __version__   = '0.7.7'
        '''
        
        pxcount = svcount = 0
        pxstat = {} # {iid: {sid: svstat, ...}, ...}
    
        idx_iid = self.get_idx('iid')
        idx_sid = self.get_idx('sid')
    
        for line in iterable:
            if not line:
                continue
            if line.startswith(self.HAPROXY_STAT_COMMENT):
                continue # comment
            if line.count(self.HAPROXY_STAT_SEP) < self.HAPROXY_STAT_NUMFIELDS:
                continue # unknown format
    
            csv = line.split(self.HAPROXY_STAT_SEP, self.HAPROXY_STAT_NUMFIELDS)
    
            # Skip further parsing?
            if svcount > self.HAPROXY_STAT_MAX_SERVICES:
                try:
                    iid = csv[idx_iid]
                    iid = int(iid, 10)
                except ValueError:
                    raise RuntimeError('garbage proxy identifier: iid="%s" (need %s)' % (iid, int))
                try:
                    sid = csv[idx_sid]
                    sid = int(sid, 10)
                except ValueError:
                    raise RuntimeError('garbage service identifier: sid="%s" (need %s)' %   (sid, int))
                if iid not in pxstat:
                    pxcount += 1
                    svcount += 1
                elif sid not in pxstat[iid]:
                    svcount += 1
                continue
    
            # Parse stat...
            svstat = {} # {field: value, ...}
    
            for idx, field in self.HAPROXY_STAT_CSV:
                field_type, field_name = field
                value = csv[idx]
    
                try:
                    if field_type is int:
                        if len(value):
                            value = int(value, 10)
                        else:
                            value = 0
                    elif field_type is not type(value):
                            value = field_type(value)
                except ValueError:
                    raise RuntimeError('garbage field: %s="%s" (need %s)' % (
                            field_name, value, field_type))
    
                # Special case
                if field_name == 'status' and value == 'no check':
                    value = '-'
                elif field_name == 'check_status' and svstat['status'] == '-':
                    value = 'none'
    
                svstat[field_name] = value
    
            # Record result...
            iid = svstat['iid']
            stype = svstat['type']
    
            if stype == 0 or stype == 1:  # FRONTEND / BACKEND
                id = svstat['svname']
            else:
                id = svstat['sid']
    
            try:
                pxstat[iid][id] = svstat
            except KeyError:
                pxstat[iid] = { id: svstat }
                pxcount += 1
            svcount += 1    
        return pxstat, pxcount, svcount 
    
    
    
    def createAMI(self,instance,conn,name,description):
        try:
            print "creating a new instance ! "
            conn.create_image(instance.id, name, description, False)
            
        except Exception, e:
            print str(e)                    
             
        
if __name__ == "__main__":
        
    logging.basicConfig(filename='python.log',level=logging.DEBUG)
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    aws = AWS()
    conn=aws.connect('AKIAIE3BSOYPNK7DR5QQ', '7fBtMIiQ6pwRLic8SD4HMclDzbhmDVuogmTI96z6')
    
    
    
    if (len(sys.argv) < 2):
        logging.error("Invalid Command Arguments passed. It should be of type <Command> <Arg1> ... <Argn>")
        sys.exit(1)    
    command = str(sys.argv[1]) 
    instance = None
    
    if (command == "create"):
        try:
            logging.debug("Create Command Invoked With Params : %s" % (str(sys.argv)))
            if (len(sys.argv) < 4):
                logging.error("Invalid Command Arguments passed for create command. It should be of type  create  <Customer Name > <type of instance> <size of instance> ")
                sys.exit(1)
            name = str(sys.argv[2])
            type = str(sys.argv[3])
            size = int(sys.argv[4])         
            instance = AWS().createInstance(conn,size,name,type)
            tags = {"name":name}
            AWS().taginstance(instance, tags)
            print instance.dns_name ,"created"
        except Exception,e:
            logging.error("Exception in create command . Error : " + str(e))
            sys.exit(1)   
                 
    if (command == "monitor"):                
        print "Monitor Command Invoked With Params : %s" % (str(sys.argv))
        aws = AWS()
        if (len(sys.argv) < 3):
            print "Invalid Command Arguments passed for monitor command. It should be of type  monitor  <DNS/IP Of Instance> <Stat Type> "
        dns = str(sys.argv[2])
        stattype = str(sys.argv[3])
        while(True):
            aws.monitor(conn, dns,stattype)
            time.sleep(10)    
    
    conn.close()
#if __name__ == "__main__":
#    dns = "ec2-107-20-20-113.compute-1.amazonaws.com"
#    ab = AWS().connect(accesskey, secretkey)
#    ab = AWS().getinstance(conn)
#    
               
#        if(command == "deploy"):
#            instance_name = sys.argv[2]
#            filepath = sys.argv[2]
#            instance = AWS().getinstance(conn, instance_name)
#            #AWS().deployfiles(conn, instance, path)       
#        #AWS().getinstance(conn)
#        #instance = AWS().getinstancebyDNS(conn,'')
#        dns = 'ec2-107-22-37-61.compute-1.amazonaws.com'
#        instance = AWS().getinstance(conn, dns)
#        print instance.private_ip_address
#        #    tags = {"name":"PHP"}
#        AWS().taginstance(instance, tags)
#        #time.sleep(5)
#        cmd = "echo \"show stat\" | sudo socat unix-connect:/home/ubuntu/anand3/haproxy.sock stdio"
#        if(instance):
#            AWS().execute(conn, instance, cmd)
#            AWS().deploy(conn, instance, 'anand3')
#           # AWS().deploy(conn,instance,'anand3')       
#        #AWS().stopinstance(conn, dns)
        
