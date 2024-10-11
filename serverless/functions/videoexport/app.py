import json
import os
import subprocess
import boto3
from better_ffmpeg_progress import FfmpegProcess

SIGNED_URL_TIMEOUT = 60



def lambda_handler(event, context):
  print("Trigger event ----->", event)

  ws_conn_id = event['requestContext']['connectionId']
  ws_endpoint = os.getenv('WsEndpoint')
  progress_handler = ProgressHandler(ws_conn_id=ws_conn_id)
  print('websocket connecction id ----------> ', ws_conn_id)
  print('WsEndpoint -------------------->', ws_endpoint)
  api_client = boto3.client('apigatewaymanagementapi', endpoint_url=ws_endpoint)
  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'EXPORTING_VIDEO'}))

  body = json.loads(event['body'])
  s3_video_key = body['video_key']
  s3_ass_key = body['ass_key']
  print('s3_ass_key ---->', (s3_ass_key))

  s3_source_bucket = os.getenv('BucketName')
  print("s3_source_bucket ----> ", s3_source_bucket)

  # start and end time for video clipping
  start_time = body['start_time']
  end_time = body['end_time']

  # original video width and height(iw, ihf), target width and height(sw, sh)
  sw = float(body['sw'])
  sh = float(body['sh'])
  iw = float(body['iw'])
  ih = float(body['ih'])

  s3_source_basename = os.path.splitext(os.path.basename(s3_ass_key))[0]
  print("Source basename ----> ", s3_source_basename)
  
  s3_tmp_filename = f"{s3_source_basename}_tmp.mp4"
  print("tmp filename -----> ", s3_tmp_filename)

  s3_clipped_filename = f"{s3_source_basename}_clipped.mp4"
  print("Clipped filename ---->", s3_clipped_filename)

  s3_client = boto3.client('s3')
  if "presigned_url" in body:
    s3_source_signed_url = body['presigned_url']
  else:
    s3_source_signed_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': s3_source_bucket, 'Key': s3_video_key},
        ExpiresIn=SIGNED_URL_TIMEOUT)

  print('s3_ass ---->', s3_ass_key)  
  ass_tmp=s3_client.get_object(Bucket=s3_source_bucket, Key=s3_ass_key)
  a_data = bytearray(ass_tmp['Body'].read())
  
  file = open(f"/tmp/{s3_source_basename}"+ ".ass", "wb")
  file.write(a_data)
  file.close()

  print("Source signed url ----> ", s3_source_signed_url)

  ffmpeg_cmd1 = f"ffmpeg -i \"{s3_source_signed_url}\" -ss {start_time} -to {end_time} -c:v copy -c:a copy -y /tmp/{s3_tmp_filename}"
  print("FFmpeg first command -----> ", ffmpeg_cmd1)
  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'CLIPPING_VIDEO'}))
  subprocess.call(ffmpeg_cmd1, shell=True)
  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'CLIPPED_VIDEO'}))
  
  if((ih / iw) < (sh / sw)):
    process = FfmpegProcess(["ffmpeg", '-hide_banner', '-i', f"/tmp/{s3_tmp_filename}", '-filter:v', f"crop={ih * sw / sh}:{ih},scale={sw}:{sh},ass=/tmp/{s3_source_basename}.ass", "-pix_fmt", 'yuv420p', "-y", f"/tmp/{s3_clipped_filename}"])
  else:
    process = FfmpegProcess(["ffmpeg", '-hide_banner', '-i', f"/tmp/{s3_tmp_filename}", '-filter:v', f"crop={iw * sh / sw}:{iw},scale={sw}:{sh},ass=/tmp/{s3_source_basename}.ass", "-pix_fmt", 'yuv420p', "-y", f"/tmp/{s3_clipped_filename}"])

  print('process============>', process)

  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'CROPPING_VIDEO', 'FfmpegProcess': 0}))

  ffmpeg_output_path = f'/tmp/{s3_tmp_filename}.txt'

  process.run(progress_handler=progress_handler.handle_progress_info, ffmpeg_output_file=ffmpeg_output_path, success_handler=progress_handler.handle_success, error_handler=progress_handler.handle_error)

  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'FFmpeg processing ended'}))

  s3_destination_filename = f"publish/{s3_clipped_filename}"
  print("destination_filename ----> ", s3_destination_filename)

  resp = s3_client.upload_file(f"/tmp/{s3_clipped_filename}", s3_source_bucket, s3_destination_filename)
  print("uploaded result ----> ", resp)

  resp = api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'EXPORTED_VIDEO', 'key': s3_destination_filename}))
  print("post result ----> ", resp)

  subprocess.call(f"rm -rf /tmp/{s3_tmp_filename}", shell=True)
  subprocess.call(f"rm -rf /tmp/{s3_clipped_filename}", shell=True)

  return {
    'statusCode': 200,
    'body': json.dumps('Processing complete successfully')
  }

class ProgressHandler:
    def __init__(self, ws_conn_id: str) -> None:
      self.ws_conn_id = ws_conn_id

    def handle_progress_info(self, percentage, speed, eta, estimated_filesize):
        if percentage is None:
          return
        
        print('ws connection id --------> ', self.ws_conn_id)
        print('percentage ----> ', percentage)
        ws_endpoint = os.getenv('WsEndpoint')

        api_client = boto3.client('apigatewaymanagementapi', endpoint_url=ws_endpoint)
        api_client.post_to_connection(ConnectionId=self.ws_conn_id, Data=json.dumps({'event': 'Running FFmpeg', 'key': percentage}))

    def handle_success(self):
      # Code to run if the FFmpeg process completes successfully.
      pass

    def handle_error(self):
      # Code to run if the FFmpeg process encounters an error.
      pass