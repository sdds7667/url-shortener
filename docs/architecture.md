
# The architecture of the url shortening service
### Folder structure: 
/api - contains all the relevant files for the service
	/api/app.py - contains the routing & data validation, the responses and the configuration for the application
	/api/handlers.py - contains the handlers that are actually responsible for implementing the service
	/api/models.py - contains the models that are used by the application
	/api/repos.py - contains the repositories that follow the Data Access Object pattern, as an interface to the database for the business layer
    /api/short_func.py - contains the shortening algorithm 


/migrations - contains the migrations made by running the ```flask db update``` command. 

### Working scheme

Request => Route (/api/app.py) => Handlers(/api/handlers.py) => Repository(/api/repos.py) => PERMANENT STORAGE

The general workflow of the app: 
The user starts typing in a url, and if the server is not down a checkbox will appear, asking if the user would like to shorten their urls with the service. If they agree, a new interface will appear, where they will be able to type in the custom company slug that they would like. Once the user has finished typing, the application will make a request to the server to reserve the slug for a set amount of time (@routes/reserve-slug). Once the user is happy with a slug, and that slug is available, the user will submit the urls for shortening (@routes/shorten/custom), which will mark the reservation as permanent. On return visits, as the form is loaded, all the previous reservations are loaded as well (@routes/slugs), and the application does not make a request to check the availability of the slugs if they are already in the list. 

The shortening algorithm: 
(api/short_func.py)
```
shorten (url) -> str:
    # Add salt to the url
    url := current_date + uuid4() + url

    # convert url to an array of numbers
    url_as_numbers := ord(i) for each character of the url
    
    shuffle url_as_numbers
    break it down into 6 chunks (6 being the length of the shortened url)

    final_url := ""
    for each chunk:
        sum := add up all the numbers of the chunk % 62 (a-zA-Z0-9)
        chunk_char = convert sum to character
        final_url := final_url + chunk_char
    
    return final_url
```

### Syncing the urls: 
Using heroku data-clips: 
There is a data-clip in the heroku postgres instance, with the following query: 
```sql
SELECT * FROM url_entry_model WHERE synced = false OR synced IS NULL;
```
This will pull all the urls out of the database that have not been synced.
To update the sync status: 
```sql
UPDATE url_entry_model
SET synced=true
WHERE synced=false or synced IS NULL;
```