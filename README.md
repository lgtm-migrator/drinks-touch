[![Build Status](https://travis-ci.org/flipdot/drinks-touch.svg?branch=master)](https://travis-ci.org/flipdot/drinks-touch)
# Drinks Scanner Display
Digital replacement for the drinks tally list featuring a touchscreen, user management and a barcode scanner.

## Deployment

### Docker
For usage with Docker you need a running X server. See below for details.

- Linux

  First, allow connections from Docker to X:
  ```bash
  xhost local:docker
  ```
  Then execute the stack:
  ```bash
  docker stack deploy -c ./stack.yml drinks-touch
  ```

  <details>
    <summary>individual DSD container instructions</summary>

    ```bash
    docker run --name dsd_drinks-touch -d -v ${PWD}/drinks_touch/config.py:/app/config.py -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix${DISPLAY} flipdot/drinks-touch
    ```
  </details>

- Windows

  As X server for Windows you can use [VcXsrv](https://sourceforge.net/projects/vcxsrv/). Be sure to check "disable access control" in the XLaunch dialog.

  ```bash
  docker stack deploy -c .\stack-windows.yml drinks-touch
  ```

  <details>
    <summary>individual DSD container instructions</summary>

    ```powershell
    docker run --name dsd_drinks-touch -d -v ./drinks_touch/config.py:/app/config.py -e DISPLAY=${env:DISPLAY} flipdot/drinks-touch
    ```
  </details>


<details>
  <summary>individual general container instructions</summary>

  ```bash
  # PostgreSQL
  docker run --name dsd_postgres -d -p 5432:5432 -v dsd_postgres-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=drinks postgres

  # Adminer
  docker run --name dsd_adminer -d -p 8080:8080 --link dsd_postgres:db adminer
  ```


  ```bash
  # OpenLDAP
  docker run --name dsd_ldap -d -p 389:389 -e LDAP_DOMAIN="flipdot.org" osixia/openldap

  # phpLDAPadmin
  docker run --name dsd_phpldapadmin -d -p 6443:443 -v dsd_phpldapadmin-data:/var/www/phpldapadmin --link dsd_ldap:ldap -e PHPLDAPADMIN_LDAP_HOSTS=ldap osixia/phpldapadmin
  ```
</details>


### Embedded

#### Dependencies
- LDAP server, reachable via `ldap://rail/` (see [users.py](drinks_touch/users/users.py))
- PostgreSQL @localhost (see [storage.py](drinks_touch/database/storage.py))
- touch display with a minimum of 480x800 px.

Install dependencies like this:

```bash
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
pip2 install -r requirements.txt
```
Then copy `drinks_touch/config.example.py` to `drinks_touch/config.py`, customizing the contents.

Now, start PostgreSQL and OpenLDAP with `systemctl start`. And finally, run the entrypoint script `drinks_touch/game.py`.

For embedded systems it is recommended to use `@reboot runGame.sh` inside a cron tab.
This starts an X server, sets various display properties and puts the application itself in a loop.


## Dashboards
Login to [Adminer](http://localhost:8080) with **database system**, **username** and **password** `postgres`, **server** `dsd_postgres` and **database** `drinks`.
Login to [phpLDAPadmin](https://localhost:6443) with **login dn** `cn=admin,dc=flipdot,dc=org` and **password** `admin`.


## Database Schema
PostgreSQL dumps can be found inside the `sql` folder along with scripts to im- and export.


## Profiling
To profile the time individual lines of code take to execute install *line_profiler*.

    pip install line_profiler

Then add @profile to the methods you are interested in.

Inside `drinks_touch`, run with

    kernprof -l game.py

And analyze results with

    python -m line_profiler game.py.lprof | less

## License
TODO
