
### Deploying to heroku

- basic heroku deployment commands: 
  1. logging in 
    ```bash
    heroku login
    ```

    2. pushing the code:
    ```bash
    heroku git:clone -a {application-name}
    ```

- add the postgress add-on:
[Heroku Postgres Add-on page](https://elements.heroku.com/addons/heroku-postgresql)
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

- add the environment variables:
Optional, could generate a random string with python:
```bash
heroku config:set UrlShortenerAllowedKey="$(echo "import uuid; print(uuid.uuid4().hex)" | python3)"
heroku config:set ReservationDurationInSeconds=900
```

Command to set the key on the server's env
```bash
heroku config:set UrlShortenerAllowedKey={key}
```

- generate the database: 
```bash
heroku run flask db upgrade
```

- ensure that at least a process is running:
```bash
heroku ps:scale web=1
```


## Ignoring preview headers

If an application creates a preview by accessing the url, the reported accessed statistics will be inaccurate. 
Some applications will set their name as the header for that request. If the header is present in 
"ignored-headers.json", the request will return the redirect, but will not increase the statistics counter. 

**File format:** *List of strings, representing the headers to check against. Works only if the headers are an exact match*

**Where to find the used headers**: 
```bash
heroku run bash
cat unique-header-logs.txt
```

