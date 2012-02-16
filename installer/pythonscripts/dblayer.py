import MySQLdb
import logging

class dblayer():
    conn = None    
    mysqlip = <IPADDRESS>   #private ip of the deployment server        
    password = 'root'
    username = 'root' 
    dbname = "db"
    table = "instances"
    logging = None
    def __init__(self):
        try:            
            logging.basicConfig(filename='/root/logs/python.log',level=logging.DEBUG)
            logging.debug("Creating Mysql Connection")
            self.conn = MySQLdb.connect(self.mysqlip, self.username, self.password, self.dbname)
            logging.debug("Mysql Connection Successful")            
        except Exception,e:
            logging.error("Mysql Connection cannot be created. Error : %s", e) 
            return None
        
    def __del__(self):
        if(self.conn != None):            
            self.conn.close()    

    def insert(self,query):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            return True
        except Exception,e:
            print e
            return False 
    
    def createdbinstance(self,email, dns, ip, type):
        logging.info("Inside dblayer:createinstance Method")
        try: 
            sql = """INSERT INTO %s (email,dns,ip,type) VALUES ('%s', '%s', '%s', '%s')""" % (self.table,email,dns,ip,type)
            logging.debug("SQL Query : %s", sql)
            cursor = self.conn.cursor()        
            cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception, e:
            logging.error("Entry Cannot be added to table. Details : %s", e)
            return False
        
    def getinstancecount(self,email,type):
        logging.info("Inside dblayer:getinstancecount method")
        try:    
            command = ""        
            if(type=="all"):
                command = "select count(*) as count from %s" % (self.table)
            else:
                command = "select count(*) as count from %s where type=\'%s\' and email=\'%s\' " % (self.table, type, email)
            cursor = self.conn.cursor()        
            cursor.execute(command)
            dataset = cursor.fetchall()
            if(dataset):
                logging.debug("Number of instance returned is %s", str(dataset[0][0]))
                return int(dataset[0][0])            
            else:
                logging.debug("Number of instance returned is 0")
                return 0                  
        except Exception, e:
            logging.error("The number of instance couldn't be retrieved. Error: %s " , str(e))
            return None
    

    def getinstancesbytype(self,email,type):
        logging.info("Inside getinstancesbytype method")
        try:    
            logging.debug("Email specified :  %s and Type specified as : %s", email, type)
            command = "select dns from %s where email=\'%s\' and type=\'%s\'" % (self.table, email, type)
            cursor = self.conn.cursor()        
            cursor.execute(command)
            dataset = cursor.fetchall()
            dnslist = []
            if(dataset):
                for data in dataset:
                    dnslist.append(data[0])    
                return dnslist              
            else:               
                return None                  
        except Exception, e:
            logging.error("The email id of customer couldn't be retrieved. Error: %s " , str(e))
            return None

    def deleteinstancebydns(self,dns):
        logging.info("Inside getinstancesbytype method")
        try:    
            command = "delete from %s where dns=\'%s\'" % (self.table,dns)
            print command
            cursor = self.conn.cursor()        
            cursor.execute(command)
            self.conn.commit()
            return True                  
        except Exception, e:
            logging.error("The email id of customer couldn't be retrieved. Error: %s ", str(e))
            return None
    
    def getemailbydns(self,dnsname):
        logging.info("Inside getemailbydnsname method")
        try:    
            command = "select email from %s where dns=\'%s\'" % (self.table, dnsname)
            cursor = self.conn.cursor()        
            cursor.execute(command)
            dataset = cursor.fetchall()
            if(dataset):    
                print dataset            
                return dataset[0][0]
            else:               
                return 0                  
        except Exception, e:
            logging.error("The email id of customer couldn't be retrieved. Error: %s ", str(e))
            return None
     

if __name__ == "__main__":    
    pass
    #db = dblayer()
    #print db.getemailbydns("abcd.abcd.com")
    #print db.deleteinstancebydns("abcd.abcd.com") 
    #db.createdbinstance("abcd@abcd.com", "abcd.abcd.com", "1.1.1.1", "mysql")
    #db.createdbinstance("test@test.com", "abcd.abcd.com", "1.1.1.1", "php")
    #print db.getinstancecount("test@test.com", "all")   
