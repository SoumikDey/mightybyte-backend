import json
import psycopg2
import os

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    # Create a Secrets Manager client
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        # Retrieve secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Parse secret string or binary
        if "SecretString" in response:
            secret_data = json.loads(response["SecretString"])
        else:
            secret_data = json.loads(response["SecretBinary"])

        # Extract values
        username = secret_data.get("username")
        password = secret_data.get("password")

        return username, password

    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None, None

# Example usage




sentry_sdk.init(
    dsn="https://5a1c0d5d05426416fb9835621ad41de5@o4508730975322112.ingest.de.sentry.io/4508730981417040",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    integrations=[AwsLambdaIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)


# Database connection parameters
DB_HOST = os.environ['DB_HOST']  # Set environment variable for your RDS hostname
DB_NAME = os.environ['DB_NAME']  # Set environment variable for your database name
DB_PORT = '5432'  # Default PostgreSQL port
secret_name = os.environ['SECRET_NAME']  # Set environment variable for your database password
region = os.environ['REGION']  # Change to your AWS region

DB_USER, DB_PASSWORD = get_secret(secret_name, region)

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',  # Allows requests from any domain
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',  # Allowed HTTP methods
    'Access-Control-Allow-Headers': 'Content-Type'  # Allow Content-Type header
}

def connect_to_db():
    """
    Establish a connection to the PostgreSQL database.
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

def create_task(event, context):
    """
    Lambda function to create a task in the PostgreSQL database.
    """
    try:
        # Get the JSON body from the event
        data = json.loads(event['body'])
        
        # Extract the 'description' field from the JSON data
        description = data.get('description', None)
        
        # Check if description is provided
        if not description:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Description is required'}),
                'headers': CORS_HEADERS  # Add CORS headers
            }
        
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()

        # Insert the task into the database
        insert_query = "INSERT INTO tasks (description) VALUES (%s) RETURNING id, created_at;"
        cursor.execute(insert_query, (description,))
        result = cursor.fetchone()

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return the response with the created task's ID and created_at timestamp
        return {
            'statusCode': 201,
            'body': json.dumps({
                'id': result[0],
                'description': description,
                'created_at': result[1].isoformat()
            }),
            'headers': CORS_HEADERS  # Add CORS headers
        }

    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)}),
            'headers': CORS_HEADERS  # Add CORS headers
        }

def get_tasks(event, context):
    """
    Lambda function to fetch all tasks from the PostgreSQL database.
    """
    try:
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()

        # Query to fetch all tasks
        select_query = "SELECT id, description, created_at FROM tasks;"
        cursor.execute(select_query)

        # Fetch all tasks from the result
        tasks = cursor.fetchall()

        # Prepare the tasks list in JSON format
        tasks_list = []
        for task in tasks:
            task_data = {
                'id': task[0],
                'description': task[1],
                'created_at': task[2].isoformat()
            }
            tasks_list.append(task_data)

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return the tasks as JSON response
        return {
            'statusCode': 200,
            'body': json.dumps(tasks_list),
            'headers': CORS_HEADERS  # Add CORS headers
        }

    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)}),
            'headers': CORS_HEADERS  # Add CORS headers
        }

def lambda_handler(event, context):
    """
    Main Lambda handler function that dispatches the requests based on the HTTP method.
    """
    print("Received event:", json.dumps(event, indent=2))

    # Handle OPTIONS method (preflight request) for CORS
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'body': '',  # Empty body for OPTIONS response
            'headers': CORS_HEADERS  # Respond with CORS headers for OPTIONS
        }

    # Handle POST and GET requests
    if event['httpMethod'] == 'POST' and event['resource'] == '/tasks':
        return create_task(event, context)
    if event['httpMethod'] == 'GET' and event['resource'] == '/tasks':
        return get_tasks(event, context)
    
    return {
        'statusCode': 404,
        'body': json.dumps({'message': 'Not Found'}),
        'headers': CORS_HEADERS  # Add CORS headers for 404 response
    }
