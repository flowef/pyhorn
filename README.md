# PyHorn

An unofficial Python client to interact with Bullhorn's REST API.
We developed this client to facilitate the integration of FLOW's systems with Bullhorn, and decided to disclose the source for any other developers that may find it useful.

## Installation

`pip install pyhorn-flow`

## Authentication

Authentication requires a simple JSON file containing the following auth-related data (provided by Bullhorn themselves):

- username
- password
- client_id
- client_secret

Other fields are filled automatically and stored in `file_name` for better use of the authenticated session.

```json
{
 "file_name": "auth.json",
 "client_id": "GUIDprovidedbybullhorn",
 "client_secret": "secretprovidedbybullhorn",
 "username": "apiuser",
 "password": "yourpasswordshouldgohere"
}
```

## Supported Functions

- Ping
- Search
- Query
- Entity
  - Create
  - Update
  - Delete
- To-many
  - Create association
  - Delete association

## Changelog

### v1.0

- Added safe request to re-authorize requests when 401 is returned from API
- Added Entity creation, update and deletion
- Added To-many association and dissociation
- Added Search and Query functionalities
- Added Ping functionality and automatic session renewal
- Added authentication flow
