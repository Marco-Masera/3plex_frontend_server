#!bin/bash


export BACKEND_SERVER_URL='http://127.0.0.1:5000'

#Safe variables area - To be modified and stored elsewhere
export DJANGO_SECURE_KEY='django-insecure-&0o*(s9@=kl=)_*+^^#g4(d-aynnwwyci(642zg52lqi7y4#zv'
export HMAC_KEY="YOU_WISH_YOU_KNEW_MY_SECRET_KEY!"

export DEBUG=0
export ALLOWED_HOSTS="192.168.99.164,www.3plex.unito.it,3plex.unito.it"

export PUBLIC_API_PATH="api/"
export PRIVATE_API_PATH="results/"
export ADMIN_PATH="admin/"

#File management config
export SSRNA_BASE_NAME="ssRNA.fa" #all ssRNA.fa file will be renamed to this
export DSDNA_BASE_NAME="dsDNA.fa" #same with dsDNA_fasta
export DSDNA_BED_BASE_NAME="dsDNA.bed" #same with dsDNA_fasta
export SSRNA_HEADER="ssRNA"
#Files and urls
export FILE_UPLOAD_MAX_MEMORY_SIZE=4000000
export DSDNA_MAX_SIZE=3000000000
export SSRNA_MAX_SIZE=2000000
export MEDIA_ROOT="/home/mamasera/3plex_media_root"
export MEDIA_URL="3plex/results/"
export CLIENT_URL="https:www.3plex.unito.it/"

#Cleanup service
export RUN_CLEANUP_EVERY_HOURS=24
export CLEANUP_AFTER_HOURS=168
#Email config
export EMAIL_USE_TLS=1
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_HOST_USER="3plex.service@gmail.com" 
export EMAIL_HOST_PASSWORD="fujkmmbadequheof"  #  'Pippo123'
export EMAIL_PORT=587

#Admin
export ADMINS="Marco,marco.masera@unito.it;Altro_Admin,altro_admin_mail@unito.it"

# Application definition
export CORS_ALLOW_ALL_ORIGINS=1

#Database
export DATABASE_ENGINE="mysql"
export DATABASE_NAME="triplex"
export DATABASE_USERNAME="root"
export DATABASE_PASSWORD="triplex"
export DATABASE_HOST="db"
export DATABASE_PORT=3306