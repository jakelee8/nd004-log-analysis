#!/usr/bin/env python3

import argparse
import sys

from urllib.parse import urlunsplit, quote as urlquote
from sqlalchemy import create_engine

try:
    MAX_INT = sys.maxsize  # Python 2
except AttributeError:
    MAX_INT = sys.maxint  # Python 2


POPULAR_ARTICLE_SQL = '''\
SELECT id, views, title FROM (
  SELECT path, count(*) AS views
    FROM log
    WHERE substring(path, 0, 10) = '/article/'
    GROUP BY path
    ORDER BY views DESC
    LIMIT 3
  ) AS article_views
  INNER JOIN articles
  ON concat('/article/', articles.slug) = article_views.path;'''

POPULAR_AUTHOR_SQL = '''\
SELECT id, name, views FROM (
  SELECT author, sum(views) as views
    FROM (
    SELECT path, count(*) AS views
      FROM log
      WHERE substring(path, 0, 10) = '/article/'
      GROUP BY path
    ) AS article_views
    INNER JOIN articles
    ON article_views.path = concat('/article/', articles.slug)
    GROUP BY author
  ) AS author_views
  INNER JOIN authors
  ON author_views.author = authors.id
  ORDER BY views DESC
  LIMIT {:d};'''

ERROR_DAYS_SQL = '''\
SELECT error_counts.date as date, error_count, ok_count
  FROM (
    SELECT date_trunc('day', time) as date, count(*) as ok_count
      FROM log
      WHERE status = '200 OK'
      GROUP BY date
  ) AS error_counts
  LEFT OUTER JOIN (
    SELECT date_trunc('day', time) as date, count(*) as error_count
      FROM log
      WHERE status != '200 OK'
      GROUP BY date
  ) AS ok_counts
  ON error_counts.date = ok_counts.date
  WHERE 100 * error_count > error_count + ok_count
  ORDER BY date DESC
  LIMIT {:d};'''


def build_parser():
    """Build argument parser.

    Returns:
        Argument parser.
    """
    parser = argparse.ArgumentParser(
        description='Analyze website logs and print the results.')
    parser.add_argument(
        '--host', dest='hostname', default='localhost',
        help='PostgreSQL hostname (default: localhost)')
    parser.add_argument(
        '--port', dest='port', type=int, default=5432,
        help='PostgreSQL port (default: 5432)')
    parser.add_argument(
        '--user', dest='username', default='postgres',
        help='PostgreSQL username (default: postgres)')
    parser.add_argument(
        '--password', dest='password', default='',
        help='PostgreSQL password')
    parser.add_argument(
        '--database', dest='database', default='news',
        help='PostgreSQL database (default: news)')
    parser.add_argument(
        '--limit', dest='limit', type=int, default=MAX_INT,
        help='Limit number of results for each sub-report')

    return parser


def build_db_url(args):
    """Builds SQLAlchemy URL from arguments.

    Given command line arguments returns, for example

        postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]

    Args:
        args: command line arguments
    Returns:
        SQLAlchemy URL for a PostgreSQL database.
    """

    # Build netloc
    netloc = args.hostname

    # Add port to netloc
    if args.port:
        netloc = '{}:{}'.format(netloc, args.port)

    # Add username and password to netloc
    if args.username:
        username = urlquote(args.username)
        if args.username:
            password = urlquote(args.password)
            netloc = '{}:{}@{}'.format(username, password, netloc)
        else:
            netloc = '{}@{}'.format(username, netloc)

    db_url = urlunsplit((
        'postgresql',  # scheme
        netloc,  # netloc
        '/{}'.format(args.database),  # path
        '',  # query
        '',  # fragment
    ))

    return db_url


def _run_report(conn, sql, on_success, failure_message):
    """Runs SQL query and prints the result.

    Args:
        conn: A SQLAlchemy connection
        sql: A SQL query
        on_success: A formatting function to apply on each result row
        failure_message: A message to print if there are no results
    """
    # Execute SQL
    result = conn.execute(sql)
    # If there are results
    if result.rowcount:
        for row in result:
            # Format and print the results
            print('  {}'.format(on_success(**row)))
    else:
        # Print failure message
        print('  {}'.format(failure_message))


def answer_questions(conn, limit=MAX_INT):
    """Answers report questions.

    Prints a report answering these three queries:

    1. What are the most popular three articles of all time?
    2. Who are the most popular article authors of all time?
    3. On which days did more than 1% of requests lead to errors?

    Args:
        conn: SQLAlchemy connection
    """

    # Answer question 1
    print('The most popular three articles of all time:')

    # Run and print answer for question 1
    _run_report(conn, POPULAR_ARTICLE_SQL,
                '{title} ({views} views)'.format,
                '  No popular articles to report.')

    print()

    # Answer question 2
    print('The most popular article authors of all time:')

    # Run and print answer for question 2
    _run_report(conn, POPULAR_AUTHOR_SQL.format(limit),
                '{name} ({views} views)'.format,
                'No popular authors to report.')

    print()

    # Answer question 3
    print('Days with more than 1% of requests leading to errors:')

    # Define formatting function for question 3
    def format_error_days(**row):
        date = row['date'].date()
        rate = 100. * row['error_count']
        rate /= row['error_count'] + row['ok_count']
        return '{date} ({rate:0.2f}% error)'.format(date=date, rate=rate)

    # Run and print answer for question 3
    _run_report(conn, ERROR_DAYS_SQL.format(limit),
                format_error_days,
                '  No error days to report.')

    print()


def main(args=None):

    # Build argument parser
    parser = build_parser()

    # Parse command line arguments
    args = parser.parse_args(args=args)

    # Build SQLAlchemy URL
    db_url = build_db_url(args)

    # Log connection URL
    print('Connecting to', db_url)
    print()

    # Prepare SQLAlchemy engine
    engine = create_engine(db_url)
    try:

        # Connect to PostgreSQL
        conn = engine.connect()
        try:

            # Begin transaction
            txn = conn.begin()

            # Answer report questions
            answer_questions(conn, args.limit)

        finally:

            # End transaction without committing changes
            txn.close()

    finally:

        # Dispose SQLAlchemy engine
        engine.dispose()


if __name__ == '__main__':
    main()
