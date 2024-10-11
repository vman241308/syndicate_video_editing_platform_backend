import json
import os
import boto3

SIGNED_URL_TIMEOUT = 60

def lambda_handler(event, context):
  print("Trigger event ----->", event)

  ws_conn_id = event['requestContext']['connectionId']
  ws_route_key = event['requestContext']['routeKey']
  # body = json.loads(event['body'])

  s3_client = boto3.client('s3')
  s3_bucket_name = os.getenv('BucketName')

  if ws_route_key == '$connect':
    # app_id = body['app_id']
    print(f"WebSocket Connected -------------> {ws_conn_id}")
    # object = s3_client.Object(
    #   bucket_name=s3_bucket_name, 
    #   key=f"websocket/{app_id}"
    # )
    # object.put(Body=ws_conn_id)
  elif ws_route_key == '$disconnect':
    print(f"WebSocket Disconnected -------------> {ws_conn_id}")
    # app_id = body['app_id']
    # object = s3_client.Object(
    #   bucket_name=s3_bucket_name, 
    #   key=f"websocket/{app_id}"
    # )
    # object.delete()
  elif ws_route_key == 'exportVideo':
    print(f"WebSocket ExportVideo Event -------------> {ws_conn_id}")
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
      FunctionName=os.getenv('VideoExportFunctionName'),
      InvocationType='Event',
      Payload=json.dumps(event).encode('utf-8')
    )
    print(f"Invoke result ----> {response}")

  elif ws_route_key == 'uploadVideo':
    print(f"WebSocket UploadVideo Event -------------> {ws_conn_id}")
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
      FunctionName=os.getenv('VideoUploadFunctionName'),
      InvocationType='Event',
      Payload=json.dumps(event).encode('utf-8')
    )
    print(f"Invoke result ----> {response}")

  else:
    print(f"WebSocket Default Event -------------> {ws_conn_id}")

  return {
    'statusCode': 200,
    'body': json.dumps('Processing complete successfully')
  }
