
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
```bash
heroku config:set UrlShortenerAllowedKey={a-very-secure-key}
```

- generate the datbase: 
```bash
heroku run flask db upgrade
```

- ensure that at least a process is running:
```bash
heroku ps:scale web=1
```




