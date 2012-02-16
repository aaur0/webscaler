homeDir="/root/"
sudo mkdir $homeDir/logs/
sudo chmod 777 $homeDir/logs/
sudo apt-get install python-paramiko --assume-yes 
sudo apt-get install subversion --assume-yes 
sudo apt-get install socat --assume-yes 
sudo apt-get install python-paramiko --assume-yes 
sudo apt-get install python-mysqldb --assume-yes  
sudo svn checkout https://github.com/boto/boto/trunk  
cd $homeDir/installer/shellscripts/trunk
sudo python $homeDir/installer/shellscripts/trunk/setup.py install
sudo chmod 600 $homeDir/installer/pythonscripts/ag2.pem 

