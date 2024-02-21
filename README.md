# FC-EMTCT Portal

This is repo contains FC-EMTCT web application which a portal to be used by data clerks to update EMTCT
beneficiaries' appointment dates in FamilyConnect.

## Uisng .env

After running pip install -r requirements.txt
Create the .env file at the root of the project
Add Values for the following variables

## DEBUG must be False in Production deployment

## Django secret Key

SECRET_KEY=

## FamilyConnectServer URL

SERVER_URL=

## FamilyConnectServer API Key

API_KEY=

## Name of Database

DB_NAME=

## Database User name

DB_USER=postgres

## Database User Password

DB_PASSWORD=

## Super User URL ending with /

SUPERUSER_URL=

## Hosts

ALLOWED_HOSTS=

## Sample .env

SECRET_KEY=yUmuJbbE77lzJAjhR7GxUhMkuJHMeIBJSj_UidaHIVo
SERVER_URL=http://xxxxxxxxx.cccccc.gggg.health.go.ug
API_KEY=X6038fcf80a3d8c8088f796ff0302b3462007b7X
DB_NAME=emtct_proddb
DB_USER=postgres
DB_PASSWORD=123456
SUPERUSER_URL=eee/
ALLOWED_HOSTS=x.x.x.x
