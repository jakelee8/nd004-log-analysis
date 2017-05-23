# Log Analysis

This is my submission to the Logs Analysis Project for the Full Stack
Engineering Nanodegree at Udacity. The report tool is available at
`report.py`. The tool answers these three questions:

  1. What are the most popular three articles of all time?
  2. Who are the most popular article authors of all time?
  3. On which days did more than 1% of requests lead to errors?

The program is designed as a simple command line tool with fixed
functionality. The tool accepts as arguments the PosgreSQL hostname, port
number, username, password, database, and a limit for the number of results
returned for the last two questions.

The SQL queries were designed to make the most deeply nested queries also
the most restrictive. By restricting the most nested and earliest queries,
we minimize the amount of work done by the database. Likewise, inner and
outer join options are specified to further constrain the query.


## Usage

```sh
usage: report.py [-h] [--host HOSTNAME] [--port PORT] [--user USERNAME]
                 [--password PASSWORD] [--database DATABASE] [--limit LIMIT]

Analyze website logs and print the results.

optional arguments:
  -h, --help           show this help message and exit
  --host HOSTNAME      PostgreSQL hostname (default: localhost)
  --port PORT          PostgreSQL port (default: 5432)
  --user USERNAME      PostgreSQL username (default: postgres)
  --password PASSWORD  PostgreSQL password
  --database DATABASE  PostgreSQL database (default: news)
  --limit LIMIT        Limit number of results for each sub-report
```


## Example output

While `report.py` will work in the [Vagrant][vagrant]
[environment][vagrant-env], this example report was generated using
[Docker Compose][docker-compose]. This guide assumes that you have already
installed and configured Docker for use with Docker Compose. All commands
are run from the project root directory.

The first command uses Docker Compose to build and start the PostgreSQL
server in the background.

```sh
# Build and start Docker containers in the background
$ docker-compose up -d --build
Creating network "nd004loganalysis_default" with the default driver
Creating nd004loganalysis_postgres_1
Creating nd004loganalysis_client_1
```

The next command starts an interactive client shell with access to the
PostgreSQL instance. For security reasons, the PostgreSQL ports have not
been exposed externally outside of these client shells.

```sh
# Start client shell
$ docker-compose run --rm client
/data $
```

Once inside the client shell, issue the following commands to set up the
database. Remember to [download][] the `newsdata.zip` file to extract
`newsdata.sql` beforehand.

```sh
# Create news and forum databases
/data $ cat <<EOL | psql -h postgres -U vagrant
CREATE DATABASE news;
CREATE DATABASE forum;
EOL

# Import log analysis sql data
/data $ psql -h postgres -U vagrant -d news -f newsdata.sql
...

# Start PostgreSQL shell with news database selected
/data $ psql -h postgres -U vagrant -d news
psql (9.6.2, server 9.5.7)
Type "help" for help.

news=# exit
```

The database is now ready to be analyzed. The following command runs the
report script using the PostgreSQL server, exposed to the client container
by Docker Compose, with the hostname `postgres`, user `$POSTGRES_USER` from
the environmental variable set through Docker Compose, and no password.

```sh
/data $ python3 report.py --host postgres --user "$POSTGRES_USER"
Connecting to postgresql://vagrant:@postgres:5432/news

The most popular three articles of all time:
  Bad things gone, say good people (170098 views)
  Bears love berries, alleges bear (253801 views)
  Candidate is jerk, alleges rival (338647 views)

The most popular article authors of all time:
  Ursula La Multa (507594 views)
  Rudolf von Treppenwitz (423457 views)
  Anonymous Contributor (170098 views)
  Markoff Chaney (84557 views)

Days with more than 1% of requests leading to errors:
  2016-07-17 (2.26% error)

/data $ exit
```

The database and data will remain available until it is destroyed with the
next command.

```sh
$ docker-compose down
```


[vagrant]: https://www.vagrantup.com
[vagrant-env]: https://github.com/udacity/fullstack-nanodegree-vm
[docker-compose]: https://docs.docker.com/compose/
[download]: https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip
