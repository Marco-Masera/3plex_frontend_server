#!/bin/bash


echo "Running daily backup"
mkdir backup
mysqldump --host=127.0.0.1 --port=30001 -u root -ptriplex triplex > $(pwd)/backup/myDBDump
cp -r /home/mamasera/3plex_media_root/jobs $(pwd)/backup/jobs
tar -zcvf $(pwd)/$(date +%y_%m_%d)_backup.tar.gz $(pwd)/backup
rm -rf $(pwd)/backup/
