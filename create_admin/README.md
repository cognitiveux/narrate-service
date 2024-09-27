# Helper script for creating an Admin account

First, make sure that the narrate-service server solution is up and running (Follow the instructions from the ```narrate-service/server/README.md```)

## Build Docker services (for all the following steps you must be at the ```narrate-service/create_admin/``` directory)

```console
foo@bar:~$ docker-compose -f docker-compose.yml build
```

## Create and start the container

```console
foo@bar:~$ docker-compose -f docker-compose.yml up
```

Upon successful completion of the script, the Admin's account credentials will be printed on the console. Use these credentials to login as an Admin.

To create additional Admin accounts (using different configuration for the email address or the organization), modify the ```insert_admin_user``` function in the ```narrate-service/create_admin/main.py``` file.

## Stop the container and remove it

```console
foo@bar:~$ docker-compose -f docker-compose.yml down
```