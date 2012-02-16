#!/bin/sh

 ########## Editing Sudoers for apache user ################################
  line=`grep "www-data  ALL=(ALL) NOPASSWD:ALL" /etc/sudoers | wc -l`
  if [ $line -eq 0 ]
  then
  echo "www-data  ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
  fi

