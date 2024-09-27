# Instructions for local development

## Clone the repository

```console
foo@bar:~$ git clone https://github.com/cognitiveux/narrate-service
```

## Set the values for the seret keys in ```django_variables.env``` file

### Create an App password in Gmail for the purpose of sending emails

Follow the instructions [here](https://support.google.com/mail/answer/185833)

Once you have an App password, modify the following file:
```narrate-service/server/django_variables.env```

and update the values of the following variables accordingly:
```SERVER_EMAIL=YOUR_EMAIL@DOMAIN.COM```
```SERVER_EMAIL_ALIAS=YOUR_EMAIL_ALIAS@DOMAIN.COM```
```SERVER_EMAIL_PASSWORD=THE_CREATED_APP_PASSWORD```

### Set values for the remaining secret keys

You could use an online secret key generator to get random strong secret keys:

- [Avast Random Password Generator](https://www.avast.com/random-password-generator)
- [LastPass Password Generator](https://www.lastpass.com/features/password-generator)

and update the values of the following variables accordingly:
```SECRET_KEY_NARRATE_PROJECT='YOUR_PROJECT_SECRET_VALUE'```
```FLOWER_USER=YOUR_FLOWER_USERNAME_VALUE```
```FLOWER_PASSWORD='YOUR_FLOWER_SECRET_VALUE'```

## Install Docker Engine

[Docker Engine](https://docs.docker.com/engine/)

Start the Docker Engine

## Create Docker network

```console
foo@bar:~$ docker network create web
```

## Build Docker services (for all the following steps you must be at the ```narrate-service/server/``` directory)

```console
foo@bar:~$ docker-compose -f docker-compose.yml build
```

## Create and start the containers

```console
foo@bar:~$ docker-compose -f docker-compose.yml up
```

## Stop the containers without removing them

```console
foo@bar:~$ docker-compose -f docker-compose.yml stop
```

## Stop the containers and remove them

```console
foo@bar:~$ docker-compose -f docker-compose.yml down
```

## Stop the containers and remove them (also remove volumes for database data)

```console
foo@bar:~$ docker-compose -f docker-compose.yml down -v
```

## Links for local development and testing
- Website: http://localhost:10000/backend
- Documentation: http://localhost:10000/backend/doc
- Interactive Demo: http://localhost:10000/backend/demo