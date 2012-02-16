from boto.ec2.connection import EC2Connection
import os,boto
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
from boto.regioninfo import RegionInfo
import ConfigParser,io,traceback

class AWS():    
    keyfilepath = '/root/installer/key/'    
    #SSH_OPTS      = '-o StrictHostKeyChecking=no -i /root/installer/pythonscripts/akg.pem'
    prefix = "/root/"
    COPY_DIRS     = ['/root/installer', '/root/userfiles']
    instancesize = {0:"m1.small",1:"m1.large", 2:"m1.xlarge"}
    iscripts = {"php":"shellscripts/installPhp", "mysql":"shellscripts/installMySql_Server", "lb":"shellscripts/installHaProxy","basic":"../shellscripts/prepareinstance.sh"}
    processmap ={"mysql":"","php":"","haproxy":""}
    filesdir = 'installer'
    scriptsdir = 'scripts'
    haproxysockpath = '/root/haproxy.sock'
    configfilepath="//root/installer//pythonscripts//config.cfg"      
    db = None
    timer = None    
    
    def __init__(self):
        try:           
            self.db = dblayer.dblayer()
            self.config = ConfigParser.RawConfigParser( )
            if os.path.exists(self.configfilepath):
                self.config.read(self.configfilepath)
            else:
                logging.error("Config file doesn't exists")
                os.sys.exit(1)   
            self.keyfilename=self.config.get("euca", "keyfilename")            
            #self.SSH_OPTS = self.config.get("euca","SSH_OPTS")
            self.keyfilefullpath = "%s/%s" % (self.keyfilepath, self.keyfilename)
            self.SSH_OPTS  = '-o StrictHostKeyChecking=no -i %s' % self.keyfilefullpath
            self.conn = self.connect()              
            self.upscalethreshold=self.config.get("euca", "upscalethreshold")
            self.downscaletime=self.config.get("euca", "downscaletime")
        except Exception,e:
            logging.error("Error in init method:  %s",str(e))       
            os.sys.exit()
    def connect(self):
        '''
            Method to establish connection to EC2.
        '''
        conn = None
        try:
            logging.info("Inside connect method")
            aws_access_key_id_prop=self.config.get("euca", "aws_access_key_id")            
            aws_secret_access_key_prop=self.config.get("euca","aws_secret_access_key")            
            regionname=self.config.get("euca","regionname")
            endpointname=self.config.get("euca","endpoint")
            region = RegionInfo(name=regionname, endpoint=endpointname)
            conn = boto.connect_ec2(aws_access_key_id=aws_access_key_id_prop, aws_secret_access_key=aws_secret_access_key_prop, is_secure=False,region=region,port=8773,path="/services/Eucalyptus")            
            if (conn == None):                
                logging.error("Connection cannot be established. Exiting")            
                os.sys.exit()           
            
        except Exception,e:
            logging.error("Existing connect method with error %s",str(e))            
            os.sys.exit()
        logging.info("Exiting connect method")  
        return conn
    
    def createInstance(self,size,name,instancetype):
        logging.info("Inside create instance method")
        logging.info("Creating instance of type %s size %s and name %s " , instancetype, str(size), name)        
        IMAGE           = self.config.get("euca","aminame") 
        KEY_NAME        = self.config.get("euca","keyname")
        INSTANCE_TYPE   = self.instancesize[size]       
        ZONE            = self.config.get("euca","zonename") # Availability zone must match the volume's
        SECURITY_GROUP = self.config.get("euca","securitygroup") # Security group allows SSH
        SECURITY_GROUPS = [SECURITY_GROUP,]
        #SECURITY_GROUPS.append(SECURITY_GROUP)
        # Create the EC2 instance
        logging.debug("calling instance creation")        
        logging.debug('Starting an EC2 instance of type %s with image %s ',INSTANCE_TYPE, IMAGE)
        try:        
            reservation = self.conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, placement=ZONE, security_groups=SECURITY_GROUPS)
            instance = reservation.instances[0]
            time.sleep(20) # Sleep so Amazon recognizes the new instance
            while not instance.update() == 'running':
                time.sleep(5) # Let the instance start up               
            # hack to repopulate the instance object as IP Address doesn't get populated in the first run           
            
            if(instance == None):
                logging.error("The instance object is returned as None..")
                sys.exit(1)      
            id = instance.id                    
            if(id):                   
                if (self.isinstanceready(self.conn, id)):
                    instance = self.getinstancebyid(self.conn, id)
                else:
                    logging.error("Cannot find the instance. System Cannot Proceed Ahead. Halting.")             
                    sys.exit(1)
            else:
                logging.error("Instance returned as None by BOTO.")             
                sys.exit(1)                       
            #privateip =  instance.private_ip_address         
            dnsname = instance.dns_name
            if (instance.private_ip_address):
                privateip =  instance.private_ip_address
            else:
                privateip =  dnsname
            logging.debug('Started the instance: %s having IP Address : %s',dnsname, privateip)      
            if(instancetype== "mysql"):            
                os.system("echo %s=%s  >> /root/installer/shellscripts/instances.dat" % (instancetype,str(dnsname)))
                self.db.createdbinstance(name, dnsname, privateip, instancetype)
            else:
                os.system("echo %s %s %s  >> /root/installer/shellscripts/instances.dat" % (dnsname, str(privateip), instancetype))
                self.db.createdbinstance(name, dnsname, privateip, instancetype)            
            logging.debug("Check if  SSH port is open.")            
            if(self.issshportopen(dnsname)):           
                logging.debug("Copying Files ")                    
                #copy files to new instance
                for copy_dir in self.COPY_DIRS:
                    logging.debug("Copying Dir : %s " ,copy_dir)
                    command = "scp -r  {0} {1} root@{2}:/root".format(self.SSH_OPTS, copy_dir, dnsname)
                    logging.debug("Using command = %s", command)
                    #command = "rsync -e \"ssh {0}\" -avz {2} root@{1}:{3}/ > /root/logs/rsynclogfile 2>&1".format(self.SSH_OPTS, dnsname, copy_dir,"/root")
                    print command
                    logging.debug("Command Executed : %s", command)           
                    os.system(command)                   
                logging.debug("Calling Script File to install %s " , instancetype)        
                self.execute(self.conn, instance, "/root/installer/"+self.iscripts[instancetype]+" "+ name)
                logging.info("Instance created and ready for use")
                return instance
            else:
                logging.error("SSH Connection to the host cannot be established. ")
                sys.exit(1)
        except Exception, ex:
            traceback.print_exc(file=sys.stdout)            
            logging.error("Error in create instance methods. %s" , ex)
            os.sys.exit()
                
            
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
            self.execute(self.conn, instance, command)
            print "Executed command successfully"   
            # 2. copy the files from local to remote machines
            for copy_dir in self.COPY_DIRS:
                os.system(command)
            print 'File Copy completed.'           
            # execute the scripts
    
    def isinstanceready(self,conn,id):
        logging.info("Inside is instance ready Method")
        time.sleep(10)
        instance = self.getinstancebyid(conn, id)
        if(instance.dns_name <> "0.0.0.0"):
            logging.info("Dns has been populated.")
            return True
        retrycount = 5        
        while(retrycount):
            logging.debug("Unable to fetch instance object. Retry will be attempted after 5 seconds.")            
            time.sleep(10)
            instance = self.getinstancebyid(conn, id)
            if((instance.dns_name <> "0.0.0.0")):                
                logging.debug("exiting isinstancereadymethod: Instance having dns %s found.",instance.dns_name)
                return True
            retrycount = retrycount - 1
        logging.error("Instance couldn't be started. Either increase the time our or check for errors")
        return False   
            
     
    def issshportopen(self,address):
        logging.info("Inside is SSH Port Open Method for Address : %s " , address)
        retrycount = 3
        while(retrycount):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                logging.info("Trying to connect to the instance %s as user: root with key file %s",address,self.keyfilefullpath)
                ssh.connect(address, username="root", key_filename=self.keyfilefullpath)
                logging.debug("SSH Connection Successful")
                return True
            except paramiko.ChannelException,connectionfailed:
                logging.error("Connection Cannot be Established %s" , str(connectionfailed))
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" , (3-retrycount))    
                time.sleep(retrycount*5)
            except paramiko.AUTH_FAILED,authfailed:
                logging.error("Authentication Error : %s" % str(authfailed))
                retrycount = retrycount - 1
                logging.info("Retrying to establish connection.  Attempt Number :  %s" , (3-retrycount)) 
                time.sleep(retrycount*5)
            except Exception,e:
                logging.error("Connection timed out to the client. Retry will be attempted.")
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" , (3-retrycount))    
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
        time.sleep(10)
        reservations=self.conn.get_all_instances()
        for reservation in reservations:      
            for instance in reservation.instances:
                if(instance.dns_name == dns):
                    return instance
        return None
    
    def getinstancebyid(self,conn,id):
        logging.info("Inside get instance by id methods %s",id)
        id = id.strip()        
        instance_ids_list=[id,]
        time.sleep(10)
        reservations=conn.get_all_instances(instance_ids=instance_ids_list)
        if reservations <> None:
            for reservation in reservations:      
                for instance in reservation.instances:
                        logging.debug("Instance found having id : %s",id)
                        return instance
        logging.debug("Instance not found. ID : %s", id)
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
        logging.debug("Command to be Executed : nohup bash -c \"%s\" > /dev/null 2>&1 &" , str(path))        
        retrycount = 3        
        if (instance == None):
            logging.debug("Error : Invalid Instance Object")
            
        while(retrycount):
            try:                
                logging.debug("trying to setup SSH Connection")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(instance.dns_name, username="root", key_filename=self.keyfilefullpath)
                logging.debug("SSH Connection Successful")
                logging.debug("Executing Command " + command)
                stdin, stdout, stderr = ssh.exec_command(command)                
                data =  stdout.readlines()                
                logging.debug("Execution result : %s" , str(data))
                return data            
            except paramiko.ChannelException,connectionfailed:
                logging.error("Connection Cannot be Established %s" % str(connectionfailed))
                retrycount = retrycount - 1            
                logging.debug("Retrying to establish connection.  Attempt Number :  %s" , 3-retrycount)    
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
    
    def monitor(self, dns,type):
        '''
        Method to monitor instances for load
        '''
        logging.info("Inside Monitor method at : %s" , time.ctime())
        logging.debug("Fetching instance object having dns =  %s",dns)
        instance = self.getinstance(self.conn, dns)
        if(instance == None):
            logging.error("Instance doesn't exsist. Monitoring will be halted.")
            sys.exit(1)
        cmd = "echo \"show stat\" | sudo socat unix-connect:{0}".format(self.haproxysockpath)
        cmd = "sudo python /root/installer/pythonscripts/haproxy.py {0}".format(type)
        try:        
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logging.debug("Trying to connect to EC2 instance")
            ssh.connect(dns, username="root", key_filename=self.keyfilefullpath)
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
                                self.createInstance(self.conn, 1, emailid.strip(), "php")
                                # notify haproxy and restart it
                                logging.info("Notifying HaProxy.")
                                self.execute(self.conn, instance, "/root/installer/"+self.iscripts["lb"])                                                       
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
                                        logging.debug("Numer of PHP instances =  %s" , str(phpinstancecount))
                                        if(phpinstancecount > 2):                                        
                                            logging.debug("Down Scale should be triggered")
                                            #pick the instance to be killed
                                            instancetobekilled = random.randint(1,phpinstancecount-1)
                                            logging.debug("Kill the instance : %s", str(instancetobekilled))
                                            phpinstancesdnslist = self.db.getinstancesbytype(emailid, "php")
                                            targetinstancedns = phpinstancesdnslist[instancetobekilled]
                                            logging.info("Instance to be killed has DNS  : %s", targetinstancedns)                                        
                                            self.stopinstance(self.conn, targetinstancedns)
                                            # remove the entry from instances.dat
                                            commandtoremoveentry = "sudo grep -v %s /root/installer/shellscripts/instances.dat > temp" % (targetinstancedns)
                                            logging.info("Command to remove entry from Instances.dat : %s", commandtoremoveentry) 
                                            os.system(commandtoremoveentry)
                                            os.system("mv temp /root/installer/shellscripts/instances.dat")
                                            # drop entry from table
                                            res = self.db.deleteinstancebydns(targetinstancedns)
                                            #inform haproxy                                                                    
                                            logging.debug("Inform HaProxy about instance termination.")
                                            logging.debug("Calling Script File to install Haproxy")        
                                            self.execute(self.conn, instance, "/root/installer/"+self.iscripts["lb"])
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
                logging.error("Exception in Monitor method : Details %s ", str(ex))
        ssh.close()
    
    
    def downscale(self,instance):
        '''
        Method to trigger downscaling of instances        
        '''        
        
        pass
    
    
    def upscale(self,instance):
        pass
            
    
    
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
    #formatter = logging.Formatter('[%(levelname)s] %(asctime)-15s %(clientip)s %(user)-8s %(message)s')
    #FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'    
    logging.basicConfig(filename='python.log',level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')    
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    aws = AWS()
    #conn=aws.connect('UQ8GATqwbQT6v1yAvg9R3EJzZdvfPeFyDiRg', 'hGe4WCORyqEEFPRZfM7dLPqvH607IsH1a1nZw')        
    if aws == None:
        print "Cannot connect to ec2"
        sys.exit(0)
    
    if (len(sys.argv) < 2):
        logging.error("Invalid Command Arguments passed. It should be of type <Command> <Arg1> ... <Argn>")
        sys.exit(1)    
    command = str(sys.argv[1]) 
    instance = None
    
    if (command == "create"):
        try:
            logging.debug("Create Command Invoked With Params : %s" , str(sys.argv))
            if (len(sys.argv) < 4):
                logging.error("Invalid Command Arguments passed for create command. It should be of type  create  <Customer Name > <type of instance> <size of instance> ")
                sys.exit(1)
            name = str(sys.argv[2])
            type = str(sys.argv[3])
            size = int(sys.argv[4])         
            instance = aws.createInstance(size,name,type)
            tags = {"name":name}
            aws.taginstance(instance, tags)
            print instance.dns_name ,"created"
        except Exception,e:
            print e
            logging.error("Exception in create command . Error : " + str(e))
            sys.exit(1)   
                 
    if (command == "monitor"):                
        logging.debug("Monitor Command Invoked With Params : %s" ,str(sys.argv))
        aws = AWS()
        if (len(sys.argv) < 3):
            print "Invalid Command Arguments passed for monitor command. It should be of type  monitor  <DNS/IP Of Instance> <Stat Type> "
        dns = str(sys.argv[2])
        stattype = str(sys.argv[3])
        while(True):
            aws.monitor(dns,stattype)
            time.sleep(10)        
    