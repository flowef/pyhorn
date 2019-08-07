# PyHorn

A Python client to interact with Bullhorn's REST API.

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
