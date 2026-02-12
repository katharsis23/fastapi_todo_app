# Routers

This folder specifies the API handlers for the user service and task service.

## User Service

*Authorizations*: Using JWT token created by the PYJWT library in `/utils/jwt_manager.py`
*OAUTH2Scheme*: Using `OAUTH2PasswordBearer` in `/utils/oauth2_scheme.py`

### Routes

General path for user route: `/user`

#### User Authorization Routes

##### Login

*POST /user/login*: Login user
Checks the email and password against the database and returns a JWT token if successful.

```bash
curl -X 'POST' \
  'http://localhost:8000/user/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"username","password":"password","email":"email"}'
```

##### Register

*POST /user/register*: Register user
1. Creates a new user in the database
2. Creates a queue task in redis
3. Celery worker sends email
4. User verifies email using `/user/verify`
5. If verification is successful, user.is_verified is set to True
6. user got a jwt

## Avatars

### Routes v1

##### Add avatar

*POST /user/avatar*: Add avatar to user

1. Uploads avatar to external storage
2. Updates avatar_url in user.avatar_url
3. Returns avatar_url

*GET /user/avatar*:

1. Gets avatar_url from user.avatar_url
2. Returns avatar_url or default_avatar_url if None

*DELETE /user/avatar*:
