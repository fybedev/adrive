# ADrive - Simple File Sharing+
## Perfection and Idealism
This service started as a small hobby project a couple years ago, but recently I decided to renovate it and perfect it as I could. The latest version of ADrive is not perfect, definitely not perfect. However, I believe I was able to get this far believing that it could sometime be perfect.
## Installation
ADrive is completely dockerized, and is able to be ran from a simple command:
```sh
docker run -p 3133:3133 -v /folder/for/databasefiles:/app/lightdb/databases ghcr.io/fybedev/adrive
```