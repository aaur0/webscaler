import sys,os
from subprocess import *
file1 = open('NodesAdded', 'r')
line = file1.readlines()

for each_line in line:
	each_line=each_line.strip()
	cmd='date +%d%m%Y'
	p = Popen(cmd, shell=True, stdout=PIPE)
	directoryname = filename = p.communicate()[0]
	directoryname = directoryname.strip()
	#print directoryname
	#print "\n"
	command = 'rsync -a -e "ssh -l ucsb_cs276k -i ./planetlab" '+each_line+":"+"ping-traceroute-1* "+"./output_data/"+each_line;
	print command	
	os.system(command);
