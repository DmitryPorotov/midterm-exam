Author: Dmitry Porotov

---

# Brief

This project consists of a Flask web app. The app is a dashboard with a health status. The app 
is containerized using Docker. 
The project also has an `install.sh` script which builds the Docker image and configures Nginx.

# Usage

Copy `example.env` to `.env`. Set `PORT`, `VERSION` and `API_KEY` variables in the `.env` file.
If you change the `PORT` you need to also change it in the `status-dashboard.conf` file.
Run `sudo ./install.sh` to configure the Nginx server and run the app container.

# Project Structure

## Python app

The app consists of `app.py` which contains the flask application and 
`pyproject.toml` which has dependencies.

## Dockerfile

`Dockerfile` builds the image. It copies `app.py`, `pyproject.toml` into
the image. It install the dependencies from `pyproject.toml` using poetry. 
It creates a non root user to run the app.

## Nginx config file

`status-dashboard.conf` is an Nginx config file for the host machine.
The the config instructs Nginx to proxy pass the traffic to the app container.
The traffic to `/api/v1/*` is routed to `/api/v1/*`, the traffic `/api/*` is
also routed to `/api/v1/*`. If you are going to add `v2` of the API you need to
change the routing for `/api/*` to go to `/api/v2/*`.

## The install script

`install.sh` is the script that ties everything together. It reads the `.env`
file for the `PORT`, `VERSION` and `API_KEY` variables. The priority of the 
environment variables is: (1) variables passed from 
environment, (2) then variables from `.env` file, (3) then the defaults from 
the `install.sh` script itself.

After reading the variables the script builds the docker image. Then it checks
if the container already running and removes it if exists. The it runs the container
from the newly built image.

After this the script installs, enables and validates the Nginx config.
