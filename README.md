# 3plex_frontend_server

## Docs from Stabulario to be adapted - work in progress

## Installation
### Creating the db volume:
sudo docker volume create triplex_db

### Changing environment
* Environment variables for server config are set inside docker-compose.yml
* The field *DJANGO_ALLOWED_HOSTS* in the environment variables must be set to the address used to access the software, or Django will refuse connections.

### Launch docker services
* from root folder run sudo docker-compose up
* website is then accessible at http://127.0.0.1:8000/
* The database is created with an existing **admin** account with password *admin*

### Accessing shell to running server and db
To open a shell inside the running server's container use:
* sudo docker exec -ti 3plex_frontend_server-app-1 /bin/sh
To close it:
* exit
Similarly, db shell can be accessed:
* mysql --host=127.0.0.1 --port=30001 -u root -p

## Backup and restore data
### Backing up database
* For safety, it is recommended to stop the service before backing up the db.
* Run sudo docker-compose run --rm db-backup
* Backup is to be found in the ./backup directory.

### Restoring database
* **Stop the service before restoring the backup**.
* Place the backup file *triplex_db.tar.bz2* inside the ./backup directory
* Run sudo docker-compose run --rm db-restore

## Usage in debug mode - outside docker
It is possible to launch the software outside of the docker container for debug and develop purposes.
* Launch the database docker service with 
* * docker compose up -d db
* Enter in the stabulario subfolder
* Load environment variables
* * source debug_config.sh
* Create virtual environment
* * python3 -m venv env
* Activate virtual env
* * source env/bin/activate
* Install requirements into environment
* * python3 -m pip install -r requirements.txt