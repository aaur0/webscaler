from boto.ec2.connection import EC2Connection
import time
import os

class AWS():    
    SSH_OPTS      = '-o StrictHostKeyChecking=no -i /home/anand/Downloads/ag2key.pem'
    COPY_DIRS     = ['/home/anand/copyfiles']
    
    def connect(self,accesskey, secretkey):
        try:
            self.conn = EC2Connection(accesskey, secretkey)            
        except Exception,e:
            print str(e)  
        return self.conn
    
    
    def createInstance(self,conn):
        #IMAGE = 'ami-19e12d70'
        IMAGE           = 'ami-89be73e0' # Basic 64-bit Amazon Linux AMI
        KEY_NAME        = 'ag2key'
        INSTANCE_TYPE   = 'm1.small'
        #INSTANCE_TYPE   = 't1.micro'
        ZONE            = 'us-east-1a' # Availability zone must match the volume's
        SECURITY_GROUPS = ['dj'] # Security group allows SSH
        
        # Create the EC2 instance
        print 'Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE)
        #conn = EC2Connection('<aws access key>', '<aws secret key>')
        reservation = conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, placement=ZONE, security_groups=SECURITY_GROUPS)
        instance = reservation.instances[0]
        time.sleep(10) # Sleep so Amazon recognizes the new instance
     
        while not instance.update() == 'running':
            time.sleep(3) # Let the instance start up
            time.sleep(10) # Still feeling sleepy
        print 'Started the instance: {0}'.format(instance.dns_name)
        return instance
     
    def deploy(self,conn,instance,target):
        time.sleep(15)
        print 'Beginning rsync'   
        command = "mkdir {0}".format(target)
        self.execute(conn, instance, command)
        print command
        #os.system(command)             
        for copy_dir in self.COPY_DIRS:
            command = "rsync -e \"ssh {0}\" -avz --delete {2} ubuntu@{1}:{3}/ > /tmp/rsynclogfile 2>&1".format(self.SSH_OPTS, instance.dns_name, copy_dir,target)
            #AWS().execute(conn, instance, command)            
            os.system("rsync -e \"ssh {0}\" -avz --delete {2} ubuntu@{1}:{3}/ > /tmp/rsynclogfile 2>&1".format(self.SSH_OPTS, instance.dns_name, copy_dir,target))
        print 'Rsync complete'    
        #AWS().deploy(conn,instance,'anand3')
        self.execute(conn, instance, 'sudo ./anand3/copyfiles/installPhp')
        #self.execute(conn, instance, 'sudo ./anand3/copyfiles/installHaProxy')
        #self.execute(conn, instance, 'sudo ./anand3/copyfiles/installMySql_Server')
        self.execute(conn, instance, 'sudo cp ./anand3/copyfiles/index.php /var/www')
        command = r"curl http://{0}/{1}".format(instance.dns_name,'index.php')
        print command
        os.system(command)        
        # Rsync
        
#        print 'Beginning rsync'                
#        for copy_dir in COPY_DIRS:
#            command = "rsync -Paz --rsh \"ssh -i /home/anand/Downloads/ag2key.pem\" --rsync-path \"sudo rsync\"   /home/anand/copyfiles ubuntu@{0}:anand/".format(instance.dns_name)
#            print command
#            os.system(command)
#            os.system("rsync -e \"ssh {0}\" -avz --delete {2} ec2-user@{1}:anand/ > /tmp/rsynclogfile 2>&1".format(SSH_OPTS, instance.dns_name, copy_dir))
#        print 'Rsync complete'
#        
        # Rsync
#        SSH_OPTS        = '-o StrictHostKeyChecking=no -i /home/anand/Downloads/ag2key.pem'
#        COPY_DIRS     = ['/home/anand/copyfiles']
#        DEVICE          = '/dev/sdh'
#
        
        
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
                print
                
    def getinstance(self,conn,dns):
        reservations=conn.get_all_instances()
        for reservation in reservations:      
            for instance in reservation.instances:
                if(instance.dns_name == dns):
                    return instance
        return None
    
    def stopinstance(self,conn, dns):
        print 'Stopping instance'
        instance = self.getinstance(conn, dns)
        instance.stop()
        
    def execute(self, conn, instance, path):
        print "Execution Command: {0} ".format(path)
        command = "ssh -t {0} ubuntu@{1} \"{2}\"".format(self.SSH_OPTS, instance.dns_name, path)
        print command
        os.system(command)
        print "Command Executed"

conn=AWS().connect('AKIAIE3BSOYPNK7DR5QQ', '7fBtMIiQ6pwRLic8SD4HMclDzbhmDVuogmTI96z6')
#AWS().getinstance(conn)
#instance = AWS().createInstance(conn)
#instance = AWS().getinstancebyDNS(conn,'')
dns = 'ec2-107-20-34-131.compute-1.amazonaws.com/'
instance = AWS().getinstance(conn, dns)
#time.sleep(5)
cmd = "echo \"show stat\" | sudo socat unix-connect:/home/ubuntu/anand3/haproxy.sock stdio"
if(instance):
    AWS().execute(conn, instance, cmd)
   # AWS().deploy(conn,instance,'anand3')
    
#AWS().stopinstance(conn, dns)
