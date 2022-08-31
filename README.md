# Python-Flask-REST-API for Actor/Actress
TV Maze API Project using Python Flask

This project is a Flask-Restx data service that allows a client to read and store information about actors/actresses, 
and allows the consumers to access the data through a REST API. SQLite is used to store the data locally.
SQLAlchemy Core is used to perform CRUD operations on the database.

This project was submitted as an Assignment component of COMP9321 - Data Services Engineering during Term 1 2022 at UNSW, Sydney.

This is based on The TV Maze API, which provides a detailed list of TV shows and people.

You can explore the TVmaze API using the following links

The source URL: http://api.tvmaze.com/

Documentations on API Call Structure: https://www.tvmaze.com/api

## REST API Endpoints

### 1. Add a new Actor

This operation can be considered as an on-demand 'import' operation to get the details of an actor to store them in your application. 
The service will download the JSON data for the given actor/actress (by its name).


#### **Example Interface:**

POST /actors?name=brad pitt

#### **Example Response:**

: 201 Created
```json
{
    "id" : 123,  
    "last-update": "2021-04-08-12:34:40",
    "_links": {
        "self": {
          "href": "http://[HOST_NAME]:[PORT]/actors/123"
        }
    }
}
```

Note:

Imports an actor only if only the given name fully matches (ignoring cases, and any character except the English alphabet, SPACE, and numbers). 
Before sending the name to tvmaze API, replaces all non-English characters  (e.g., , -. _, ?) with Space and then send it to the API. 
No duplicate Actor names allowed.



### 2. Retrieve a new Actor

This operation retrieves an actor by their ID.


#### **Example Interface:**

GET /actors/{id}

#### **Example Response:**
```json
{  
   "id": 124,
   "last-update": "2022-03-08-12:34:40",
   "name": "Some One",
   "country": "Australia",
   "birthday": "22-05-1987",
   "deathday": null,
   "shows": [
        "show 1",
        "show 2",
        "show 3"
    ],
  "_links": {
        "self": {
          "href": "http://[HOST_NAME]:[PORT]/actors/124"
        },
        "previous": {
          "href": "http://[HOST_NAME]:[PORT]/actors/123"
        },
        "next": {
          "href": "http://[HOST_NAME]:[PORT]/actors/125"
        }
      } 
}
```


### 3. Deleting an Actor

This operation deletes an existing actor from the database.


#### **Example Interface:**

DELETE /actors/{id}

#### **Example Response:**

Returns: 200 OK
```json
{ 
    "message" :"The actor with id 134 was removed from the database!",
    "id": 134
}
```


### 4. Update an Actor

This operation partially updates the details of a given Actor.


#### **Example Interface:**
```json
PATCH /actors/{id}
{  
   "name": "Some One",
   "country": "Australia",
   "birthday": "22-05-1987",
   "deathday": null
}
```

#### **Example Response:**

Returns: 200 OK
```json
{  
    "id" : 123,  
    "last-update": "2021-04-08-12:34:50",
    "_links": {
        "self": {
          "href": "http://[HOST_NAME]:[PORT]/actors/123"
        }
    }
}
```


### 5. Retrieve the list of available Actors

This operation retrieves all available actors. 


#### **Example Interface:**

GET /actors?order=<CSV-FORMATED-VALUE> & page=1 & size=10 & filter=<CSV-FORMATED-VALUE>

 All four parameters are optional with default values being "order=+id", "page=1", and "size =10", filter="id,name". "page" and "size" are used for pagination; "size" shows the number of actors per page. "order" is a comma-separated string value to sort the list based on the given criteria. The string consists of two parts: the first part is a special character '+' or '-' where '+' indicates ordering ascendingly, and '-' indicates ordering descendingly. The second part is an attribute name which is one of {id, name, country, birthday, deathday, last-update}.

 "filter" is also another comma-separated value (id, name, country, birthday, deathday, last-update, shows), and shows what attribute should be shown for each actor accordingly.


#### **Example Response:**

 Returns: 200 OK
```json
{
    "page": 1,
    "page-size": 10,
    "actors": [ 
           { 
            "id" : 1,
            "name" : "Brad Pitt"
            },
           { 
            "id" : 2,
            "name" : "Angelina Jolie"
           },
           ...
        ],
    "_links": {
        "self": {
          "href": "http://[HOST_NAME]:[PORT]/actors?order=+id&page=1&size=10&filter=id,name"
        },
        "next": {
          "href": "http://[HOST_NAME]:[PORT]/actors?order=+id&page=2&size=10&filter=id,name"
        }
      }
}
```

### 6. Get the statistics of the existing Actors

This operation returns the statistics of existing actors in the form of json or image.


#### **Example Interface:**

GET /actors/statistics?format=json&by=country,gender

This operation accepts a parameter called "format" which can be either "json" or "image". In case when the format is an image, your operation should return an image (can be in any image format) and the image illustrates the requested information in a visualization. 

* Actors break down by an attribute determined by the "by" parameter (a comma-separated value); this parameter can be any of the following Actors' attributes: "country" (showing the percentage of actors per country), "birthday", "gender", and "life_status" (represents what percentages of actors are alive). You may decide to use different types of charts based on the given attribute.

* Total Number of actors

* Total Number of actors updated in the last 24 hours


#### **Example Response:**

Returns: 200 OK
```json
{ 
   "total": 1241,
   "total-updated": 24,
   "by-country" : { "Australia": 60.7, "USA": 19.2, ... },
   "by-gender" : { "Male": 48.6, "Femail": 51.4}
}
```
