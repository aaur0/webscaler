import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
dns = "ec2-174-129-165-245.compute-1.amazonaws.com"
pathtokey = "/home/anand/ag2.pem"
ssh.connect(dns, username="ubuntu", key_filename=pathtokey)
stdin, stdout, stderr = ssh.exec_command("uptime")
#stdout.readlines()
for line in stdout.readlines():
    print line
ssh.close()
