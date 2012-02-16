import os
from boto.ec2.connection import EC2Connection
import time
 
IMAGE           = 'ami-8e1fece7' # Basic 64-bit Amazon Linux AMI
KEY_NAME        = 'takaitra-key'
INSTANCE_TYPE   = 't1.micro'
VOLUME_ID       = 'vol-########'
ZONE            = 'us-east-1a' # Availability zone must match the volume's
SECURITY_GROUPS = ['rsync'] # Security group allows SSH
SSH_OPTS        = '-o StrictHostKeyChecking=no -i /home/takaitra/.ec2/takaitra-aws-key.pem'
BACKUP_DIRS     = ['/etc', '/opt/', '/root', '/home', '/usr/local', '/var/www']
DEVICE          = '/dev/sdh'
 
# Create the EC2 instance
print 'Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE)
conn = EC2Connection('<aws access key>', '<aws secret key>')
reservation = conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, placement=ZONE, security_groups=SECURITY_GROUPS)
instance = reservation.instances[0]
time.sleep(10) # Sleep so Amazon recognizes the new instance
while not instance.update() == 'running':
    time.sleep(3) # Let the instance start up
time.sleep(10) # Still feeling sleepy
print 'Started the instance: {0}'.format(instance.dns_name)
 
# Attach and mount the backup volume
print 'Attaching volume {0} to device {1}'.format(VOLUME_ID, DEVICE)
volume = conn.get_all_volumes(volume_ids=[VOLUME_ID])[0]
volumestatus = volume.attach(instance.id, DEVICE)
while not volume.status == 'in-use':
    time.sleep(3) # Wait for the volume to attach
    volume.update()
time.sleep(10) # Still feeling sleepy
print 'Volume is attached'
os.system("ssh -t {0} ec2-user@{1} \"sudo mkdir /mnt/data-store && sudo mount {2} /mnt/data-store\"".format(SSH_OPTS, instance.dns_name, DEVICE))
 
# Rsync
print 'Beginning rsync'
for backup_dir in BACKUP_DIRS:
    
    os.system("sudo rsync -e \"ssh {0}\" -avz --delete {2} ec2-user@{1}:/mnt/data-store{2}".format(SSH_OPTS, instance.dns_name, backup_dir))
print 'Rsync complete'
 
# Unmount and detach the volume, terminate the instance
print 'Unmounting and detaching volume'
os.system("ssh -t {0} ec2-user@{1} \"sudo umount /mnt/data-store\"".format(SSH_OPTS, instance.dns_name))
volume.detach()
while not volume.status == 'available':
    time.sleep(3) # Wait for the volume to detatch
    volume.update()
print 'Volume is detatched'
print 'Stopping instance'
instance.stop()


#rsync -Paz --rsh "ssh -i KEYPAIR.pem" --rsync-path "sudo rsync"   LOCALFILES ubuntu@HOSTNAME:REMOTEDIR/