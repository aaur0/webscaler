#Script to extract bandwidth of TCP1,TCP2,CBR from trace
#Calculate Drop rate also
import os
file1 = open('NodesAdded', 'r')
line = file1.readlines()

for each_line in line:
	each_line=each_line.strip()
	upload_code='mycron ping-traceroute.py cron-assign2.sh'
	#'/directoryname_here'
	#print each_line	
	command = 'scp -i /home/vaibhav/.ssh/id_rsa mycron ucsb_cs276k@'+each_line+':~'	
	print command
	os.system(command);
	command = 'scp -i /home/vaibhav/.ssh/id_rsa  ping-traceroute.py ucsb_cs276k@'+each_line+':~'	
	print command
	os.system(command);
	command = 'scp -i /home/vaibhav/.ssh/id_rsa  NodesAdded ucsb_cs276k@'+each_line+':~'	
	print command
	os.system(command);
	command = 'scp -i /home/vaibhav/.ssh/id_rsa assign2.sh ucsb_cs276k@'+each_line+':~'	
	print command
	os.system(command);
	ssh_command='ssh -l ucsb_cs276k -i /home/vaibhav/.ssh/id_rsa '+each_line+' -q -o StrictHostKeyChecking=no \' sh assign2.sh </dev/null >nohup.out 2>&1 &  \''
	print ssh_command
	os.system(ssh_command);
