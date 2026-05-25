import boto3
import time

# --- Configuration ---
PROFILE_NAME = "JFS-JFL-Athena-DL-PII"
DATABASE = "jfl_silver_dev"
REGION = "ap-south-1"

def run_athena_query():
    # 1. Initialize session
    session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION)

    # DEBUG: Verify who this script is actually running as
    sts = session.client('sts')
    identity = sts.get_caller_identity()['Arn']
    print(f"Running as Identity: {identity}")

    athena = session.client('athena')

    # 2. Start the query using WorkGroup instead of explicit S3 path
    # This uses the same settings the AWS Console and CLI usually use
    try:
        response = athena.start_query_execution(
            QueryString="SELECT 1;",
            QueryExecutionContext={'Database': DATABASE},
            WorkGroup='primary'  # Most accounts use 'primary'. Change if you have a custom one.
        )
    except Exception as e:
        print(f"Error starting execution: {e}")
        return

    execution_id = response['QueryExecutionId']
    print(f"Query Started. Execution ID: {execution_id}")

    # 3. Wait for completion
    while True:
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status['QueryExecution']['Status']['State']

        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    # 4. Results
    if state == 'SUCCEEDED':
        results = athena.get_query_results(QueryExecutionId=execution_id)
        for row in results['ResultSet']['Rows']:
            print([val.get('VarCharValue', 'NULL') for val in row['Data']])
    else:
        # Detailed error logging
        error_details = status['QueryExecution']['Status']
        print(f"Query {state}!")
        print(f"Reason: {error_details.get('StateChangeReason')}")

        # This will show if the error is coming from Athena or S3
        if 'Athena' in str(error_details):
            print("Check Athena Workgroup permissions.")
        elif 'S3' in str(error_details):
            print("Check S3 Bucket Policy / Encryption permissions.")

if __name__ == "__main__":
    run_athena_query()