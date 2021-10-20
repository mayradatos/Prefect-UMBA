How this project was created

Installed pipenv

```sh
pip install --user pipenv
```

Installed prefect

```sh
pipenv install
```

This created `Pipfile` file

Be advised by default prefect noiw installs "Prefect Orion" a new generation workflow orchestration engine. Docs and implementation differ. Link is
here:
https://orion-docs.prefect.io/
However it is still in technical preview and changes are expected.

Check that prefect core is installed

```
prefect version
```

Start server up with

```
prefect server start --expose
```

Or have it generate a docker-compose file with

```
prefect server config --expose > docker-compose.yaml
```

the `--expose` flag binds services to `0.0.0.0` instead of `localhost`

Bring services up with

```
docker-compose up -d
```

If server was brought up using docker-compose then tenant must be created with

```
prefect server create-tenant --name "Default"
```

Then, bring agents up (not necesarily in the same machine)

```
prefect agent <AGENT TYPE> start --api <API ADDRESS>
```

`<agent type>` = `local`

where api address is the machine with server up, must have `:4200`

A new config file must be created to have prefect point to the server

```
$ cat ~/.prefect/backend.toml
backend = "server"

$ cat ~/.prefect/config.toml
[server]
host = "http://<IP-ADDRESS>"
```

or

```
prefect backend server
```

verify this by running

```
prefect diagnostics
```

Then the flows can be registered

```
prefect register --project "Test" --path helloworld.py --watch
```

Docker agent was started with

```
prefect agent docker start --name "Docker Agent" --network prefect-server
```
