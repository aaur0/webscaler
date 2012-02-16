sudo apt-get install python-paramiko  > /tmp/prepareinstance 2>&1
sudo apt-get install subversion >> /tmp/prepareinstance 2>&1
sudo apt-get install socat  >> /tmp/prepareinstance 2>&1
sudo apt-get install python-paramiko >> /tmp/prepareinstance 2>&1
sudo apt-get install python-mysqldb >> /tmp/prepareinstance 2>&1
sudo svn checkout https://github.com/boto/boto/trunk  >> /tmp/prepareinstance 2>&1
cd /home/ubuntu/installer/shellscripts/trunk
sudo python /home/ubuntu/installer/shellscripts/trunk/setup.py install >> /tmp/prepareinstance 2>&1
chmod 600 /home/ubuntu/installer/pythonscripts/ag2.pem >> /tmp/prepareinstance 2>&1
