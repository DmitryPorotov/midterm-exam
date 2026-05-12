Author: Dmitry Porotov

---

# Brief

This project consists of a Flask web app. The app is containerized using Docker. 
The project also has an `install.sh` script which builds the Docker image and configures Nginx.

# Usage

Copy `example.env` to `.env`. Set `PORT`, `VERSION` and `API_KEY` variables in the `.env` file.
If you change the `PORT` you need to also change it in the `status-dashboard.conf` file.
Run `sudo ./install.sh` to configure the Nginx server and run the app container.