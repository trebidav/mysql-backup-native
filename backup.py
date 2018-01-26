#!/usr/bin/env python3

import yaml
import os
from datetime import datetime
import sys
import argparse
import pwd
import grp
import subprocess

parser = argparse.ArgumentParser(description='MySQL Backup Script using Docker')
parser.add_argument('--hostfile', nargs='?', metavar='file', help='YAML hostfile path - default: ./hosts.yaml', default=os.path.dirname(sys.argv[0])+"/hosts.yaml")
parser.add_argument('--backupdir', nargs='?', metavar='directory', help='Directory where backups will be stored (created if needed) - default: ./backup', default=os.path.dirname(sys.argv[0])+"/backup")
parser.add_argument('--user', nargs='?', metavar='username', help='User who will own the backup files - default: current user', default=None)
parser.add_argument('--verbose', help='Increase verbosity level', default=False, action="store_true")
args = parser.parse_args()

# Try to open and parse the hostfile

try:
    with open(args.hostfile, 'r') as hostfile:
        try: 
            hosts = yaml.load(hostfile)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)
except Exception as exc:
    print(exc)
    exit(1)


# Check if the outputdir exists and create it if necessary

try:
    path = args.backupdir.rstrip("/")
    if (not os.path.isdir(path)):
        try:
            os.makedirs(path)
        except Exception as exc:
            print(exc)
            exit(1)
except Exception as exc:
    print(exc)
    exit(1)

# Get userid and groupid

uid, gid = None, None

if (args.user is not None):
    try:
        uid = pwd.getpwnam(args.user).pw_uid
        gid = grp.getgrnam(args.user).gr_gid
    except KeyError as exc:
        print("ERROR: User not found - falling back to current user")
    except Exception as exc:
        print(exc)
        exit(1)

# One timestamp to rule them all

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")



# For every host run xtrabackup for the whole db

for host in hosts:
       
    filename = host["name"]+"-"+timestamp+".tar.gz"

    try:
    	os.system("set -o pipefail && mkdir -p "+os.path.abspath(path)+"/temp && innobackupex --user="+host["user"]+" --password="+host["password"]+" --host="+host["host"]+" --port="+str(host["port"])+" --stream=tar "+host["datadir"]+" | gzip - > "+path+"/temp/"+filename)
    	exit(1)
    except:
    	pass



    # Move the file from temp directory to the actual directory

    try:
        if (args.verbose): print("Moving file from temporary directory")
        os.rename(path+"/temp/"+filename, path+"/"+filename)
        os.rmdir(path+"/temp/")
    except Exception as exc:
        print(exc)
        exit(1)

    # create file list of backed-up files - filename;filesize;ctime
    try:
        with open(path + "/list.txt", "a") as l:
            l.write(filename + ";" + str(os.path.getsize(path + "/" + filename))+ ";" + str(os.path.getctime(path + "/" + filename)) + "\n")
    except Exception as exc:
        print(exc)

    # Chown the file to the desired user and group

    if (args.user and uid and gid):
        try:
            if (args.verbose): print("Changing owner to user \""+args.user+"\"")
            os.chown(path+"/"+filename, uid, gid)
        except Exception as exc:
            print(exc)
            exit(1)

# All is done

print("Done")
