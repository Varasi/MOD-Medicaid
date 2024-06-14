"""
datastore

Datastore handles much of the base data structures.

In Flask/single server operation, this is abstracted
by SQLAlchemy and SQLite (though one can use any 
relational database)

In AWS, a mock datastore will be created using AWS DynamoDB

"""

from sqlalchemy import Column, Integer, String, Table, MetaData, create_engine, ForeignKey

# execution_type = os.environ.get('SERVER', 'local')
metadata = MetaData()

participants = Table('participants', metadata,
    Column('via_id', Integer, primary_key=True),
    Column('epic_id', String),
    Column('epic_mrn', Integer),
    Column('last_name', String),
    Column('email', String),
    Column('phone', String),
)

trip_requests = Table('trip_requests', metadata,
    Column('atms_ride_id', String, primary_key=True),
    Column('tapi_trip_id', String),
    Column('lyft_request_payload', String),
    Column('via_trip_id', String),
    Column('via_response_payload', String),
    )

# via_confirmation = Table('via_confirmation', metadata,
#     Column('atms_ride_id', String, ForeignKey('trip_requests.atms_ride_id')),
#     Column('via_trip_id', String),
#     Column('response_payload', String),
#     )
# How will we deal with new payloads?

sqlite_db = create_engine('sqlite:///mod_db_v2.db')


if __name__ == "__main__":
    # metadata.create_all(sqlite_db)
    metadata.create_all(sqlite_db)

