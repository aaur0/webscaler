create database db;

CREATE TABLE IF NOT EXISTS db.user (
  `email` varchar(1000) NOT NULL,
  `fname` varchar(1000) NOT NULL,
  `lname` varchar(1000) NOT NULL,
  `passwd` varchar(1000) NOT NULL,
  `userid` int(10) NOT NULL,
  PRIMARY KEY (`email`)
);

CREATE TABLE IF NOT EXISTS db.plan (
  `email` varchar(1000) DEFAULT NULL,
  `planname` varchar(1000) DEFAULT NULL
);

CREATE TABLE `db`.`instances` (
`date` datetime NOT NULL,
`email` VARCHAR( 1024 ) NOT NULL ,
`dns` VARCHAR( 1024 ) NOT NULL ,
`ip` VARCHAR( 1024 ) NOT NULL ,
`type` VARCHAR( 1024 ) NOT NULL
);
