import datetime
import json
import os
import subprocess
import time
import srt
from google.cloud import speech_v1
import boto3
from pydub.utils import mediainfo
# import webvtt
from google.cloud import storage

SIGNED_URL_TIMEOUT = 60

def audio_info(audio_filepath):
    """ this function returns number of channels, bit rate, and sample rate of the audio"""

    audio_data = mediainfo(audio_filepath)
    print(audio_data)
    channels = audio_data["channels"]
    bit_rate = audio_data["bit_rate"]
    sample_rate = audio_data["sample_rate"]

    return channels, bit_rate, sample_rate

def video_info(video_filepath):
    """ this function returns number of channels, bit rate, and sample rate of the video"""

    video_data = mediainfo(video_filepath)
    print(video_data)
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate

def lambda_handler(event, context):
  print("Trigger Event ----> ", event)

  ws_conn_id = event['requestContext']['connectionId']
  ws_endpoint = os.getenv('WsEndpoint')
  print('websocket connecction id ----------> ', ws_conn_id)
  print('WsEndpoint -------------------->', ws_endpoint)
  api_client = boto3.client('apigatewaymanagementapi', endpoint_url=ws_endpoint)
  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'UPLOADING'}))

  body = json.loads(event['body'])  
  s3_source_bucket = body['bucket']
  s3_source_key = body['key']
  s3_source_basename = os.path.splitext(os.path.basename(s3_source_key))[0]

  s3_audio_filename = s3_source_basename + ".flac"

  s3_client = boto3.client('s3')
  if "presigned_url" in body: # unit test mode
    s3_source_signed_url = body['presigned_url']
  else:
    s3_source_signed_url = s3_client.generate_presigned_url('get_object',
      Params={'Bucket': s3_source_bucket, 'Key': s3_source_key},
      ExpiresIn=SIGNED_URL_TIMEOUT)
  print("Source signed url ----> ", s3_source_signed_url)
  
  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'UPLOADING_ENDED'}))

  vinfo = video_info(s3_source_signed_url)

  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'GETTING_AUDIO'}))

  ffmpeg_cmd = f"ffmpeg -i \"{s3_source_signed_url}\" -b:a {vinfo[1]} -ac {vinfo[0]} -ar {vinfo[2]} -vn -y /tmp/{s3_audio_filename}"
  print("FFmpeg command -----> ", ffmpeg_cmd)
  subprocess.call(ffmpeg_cmd, shell=True)

  s3_destination_audio_filename = f"audios/{s3_audio_filename}"
  print('-------->', s3_destination_audio_filename)

  # upload audio to s3 bucket
  resp = s3_client.upload_file(f"/tmp/{s3_audio_filename}", s3_source_bucket, s3_destination_audio_filename)
  resp = api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'UPLOADING_AUDIO', 'audio':s3_destination_audio_filename}))

  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'GETTING_AUDIO_ENDED'}))

  # create Google Cloud Bucket
  storage_client = storage.Client()
  bucket = storage_client.bucket(s3_source_bucket)
  if bucket.exists():
    print('Bucket exist ----> ', bucket.name)
  else:
    print('Creating Bucket ----> ', s3_source_bucket)
    bucket.storage_class = 'STANDARD'
    bucket = storage_client.create_bucket(bucket, location='us-central1')


  # upload to Google Cloud Bucket
  blob = bucket.blob(s3_destination_audio_filename)
  blob.upload_from_filename(f"/tmp/{s3_audio_filename}")

  ainfo = audio_info(f"/tmp/{s3_audio_filename}")

  client = speech_v1.SpeechClient()

  config = speech_v1.RecognitionConfig()
  config.language_code =  "en-US"
  config.enable_word_time_offsets = True
  config.model = 'video'
  config.enable_automatic_punctuation = True
  config.audio_channel_count = int(ainfo[0])
  config.enable_separate_recognition_per_channel = False

  audio = speech_v1.RecognitionAudio()
  audio.uri = f"gs://{s3_source_bucket}/{s3_destination_audio_filename}"

  print('--------> audiouri', audio.uri)

  request = speech_v1.LongRunningRecognizeRequest(
    config=config,
    audio=audio
  )

  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'TRANSCRIBING_SRT'}))

  operation = client.long_running_recognize(request=request)
  isDone = False
  progress = 0

  def callback(operation_future):
    nonlocal progress
    nonlocal isDone
    response = operation_future.result()
    transcriptions = []
    index = 0
    bin_size = 3 # All the words in the interval of 3 secs in result will be grouped togather.
    # print("speech to text result: -----------> ", response.results)
    # with open(f"tests/data/speech.json", "wb") as file:
    #   file.write(json.dumps(response.results))
    #   file.close()
    passed = []
    for result in response.results:
      summary = { "transcript": result.alternatives[0].transcript, "result_end_time": result.result_end_time.microseconds }
      if summary in passed:
        continue
      else:
        passed.append(summary)
      print('transcriptions summary-------------->', summary)
      print('passed ----------------------------->', passed)
      try:
        if result.alternatives[0].words[0].start_time.seconds:
          # bin start -> for first word of result
          start_sec = result.alternatives[0].words[0].start_time.seconds 
          start_microsec = result.alternatives[0].words[0].start_time.microseconds
        else:
          # bin start -> For First word of response
          start_sec = 0
          start_microsec = 0 
        end_sec = start_sec + bin_size # bin end sec
        
        # for last word of result
        last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
        last_word_end_microsec = result.alternatives[0].words[-1].end_time.microseconds
        
        # bin transcript
        transcript = result.alternatives[0].words[0].word
        
        index += 1 # subtitle index

        for i in range(len(result.alternatives[0].words) - 1):
          try:
            word = result.alternatives[0].words[i + 1].word
            word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
            word_start_microsec = result.alternatives[0].words[i + 1].start_time.microseconds # 0.001 to convert nana -> micro
            word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
            word_end_microsec = result.alternatives[0].words[i + 1].end_time.microseconds

            if word_end_sec < end_sec:
              transcript = transcript + " " + word
            else:
              previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
              previous_word_end_microsec = result.alternatives[0].words[i].end_time.microseconds
              
              # append bin transcript
              transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, previous_word_end_sec, previous_word_end_microsec), transcript))
              print('transcriptions in the middle part-------------->', transcriptions)
              # reset bin parameters
              start_sec = word_start_sec
              start_microsec = word_start_microsec
              end_sec = start_sec + bin_size
              transcript = result.alternatives[0].words[i + 1].word
              print('transcript in the middle part-------------->', transcript)
              index += 1
          except IndexError:
            pass
        # append transcript of last transcript in bin
        transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, last_word_end_sec, last_word_end_microsec), transcript))
        index += 1
        print('transcriptions in generating srt----------->', transcriptions)
      except IndexError:
        pass
      subtitles = srt.compose(transcriptions)
      print('subtitles in generating srt----------->', transcriptions)

      with open(f"/tmp/{s3_source_basename}.srt", "w") as f:
        f.write(subtitles)
        f.close()
    progress = operation.metadata.progress_percent
    api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'TRANSCRIBING_SRT', 'progress': 100}))
    isDone = True


  operation.add_done_callback(callback)


  api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'TRANSCRIBING_SRT', 'progress': 0}))

  while isDone == False:
      try:
          progress = operation.metadata.progress_percent
          print('Progress: {}%'.format(progress))
          api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'TRANSCRIBING_SRT', 'progress': progress}))
      except:
          pass
      finally:
          time.sleep(1)

  s3_destination_srt_filename = f"subtitles/{s3_source_basename}.srt"
  print('-------->', s3_destination_srt_filename)

  resp = s3_client.upload_file(f"/tmp/{s3_source_basename}.srt", s3_source_bucket, s3_destination_srt_filename)

  resp = api_client.post_to_connection(ConnectionId=ws_conn_id, Data=json.dumps({'event': 'TRANSCRIBING_SRT_ENDED', 'key':s3_destination_srt_filename}))
  
  subprocess.call(f"rm -rf /tmp/{s3_audio_filename}", shell=True)
  subprocess.call(f"rm -rf /tmp/{s3_source_basename}.srt", shell=True)

  # s3_destination_filename = f"subtitles/{s3_source_basename}.vtt"
  # webvtt.from_srt(f"/tmp/{s3_source_basename}.srt").save()
  # resp = s3.upload_file(f"/tmp/{s3_source_basename}.vtt", s3_source_bucket, s3_destination_filename)

  return {
    'statusCode': 200,
    'body': json.dumps('Processing complete successfully')
  }
