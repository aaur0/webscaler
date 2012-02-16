import MySQLdb
import logging

class dblayer():
    conn = None
    mysqlip = "ec2-174-129-49-222.compute-1.amazonaws.com"
    password = "root"
    username = "root"
    dbname = "db"
    table = "instances"
    
    def __init__(self):
        try:            
            logging.basicConfig(filename='python.log',level=logging.DEBUG)
            logging.debug("Creating Mysql Connection")
            self.conn = MySQLdb.connect(self.mysqlip, self.username, self.password, self.dbname)
            logging.debug("Mysql Connection Successful")            
        except Exception,e:
            logging.error("Mysql Connection cannot be created. Error : %s" % e) 
            return None
        
    def __del__(self):
        if(self.conn != None):
            logging.debug("Destroying Mysql Connection")
            self.conn.close()    

    def insert(self,conn,query):
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            return True
        except Exception,e:
            print e
            return False 
    
    def createdbinstance(self,email, dns, ip, type):
        logging.info("Inside createinstance Method")
        try: 
            sql = """INSERT INTO %s (email,dns,ip,type) VALUES ('%s', '%s', '%s', '%s')""" % (self.table,email,dns,ip,type)
            logging.debug("SQL Query : %s", sql)
            cursor = self.conn.cursor()        
            cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception, e:
            logging.error("Entry Cannot be added to table. Details : %s" % e)
            return False
        
   