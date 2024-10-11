from functions.videoexport import app
from contextlib import contextmanager
import json

@contextmanager
def s3_bucket(s3, bucket_name):
  s3.create_bucket(Bucket=bucket_name)
  yield

def test_videoexport(s3, bucket_name='syndicateapp', file_name='sample', file_ext='mp4'):
  with s3_bucket(s3, bucket_name):
    f = open(f"tests/data/{file_name}.{file_ext}", 'rb')
    s3.put_object(Bucket=bucket_name, Key=f"origin/{file_name}.{file_ext}", Body=f.read())
    f1 = open(f"tests/data/{file_name}.ass", 'rb')
    s3.put_object(Bucket=bucket_name, Key=f"subtitles/{file_name}.ass", Body=f1.read())
    f1.close()

    event = {
      'requestContext': {
        'connectionId': 'test-conn-id',
      }, 
      'body': json.dumps({
        'video_key':f"origin/{file_name}.{file_ext}",
        'ass_key':f"subtitles/{file_name}.ass",
        'start_time':'00:00:15',
        'end_time':'00:00:38',
        'iw':'1920',
        'ih':'892',
        'sw':'1920',
        'sh':'1080',
        'presigned_url': f"tests/data/{file_name}.{file_ext}",
      })
    }
    app.lambda_handler(event, {})
    video_object=s3.get_object(Bucket=bucket_name, Key=f"publish/{file_name}_clipped.mp4")
    v_data = bytearray(video_object['Body'].read())
    assert v_data
    file = open(f"tests/data/{file_name}_clipped.mp4", "wb")
    file.write(v_data)
    file.close()
