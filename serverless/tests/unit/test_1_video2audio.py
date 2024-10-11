from functions.video2audio import app
from contextlib import contextmanager

@contextmanager
def s3_bucket(s3, bucket_name):
  s3.create_bucket(Bucket=bucket_name)
  yield

def test_create_bucket(s3, bucket_name='syndicateapp'):
  with s3_bucket(s3, bucket_name):
    result = s3.list_buckets()
    assert len(result['Buckets']) == 1
    assert result['Buckets'][0]['Name'] == bucket_name

def test_put_object(s3, bucket_name='syndicateapp', key='syndicateapp', body='syndicateapp'):
  with s3_bucket(s3, bucket_name):
    s3.put_object(Bucket=bucket_name, Key=key, Body=body)
    object_response = s3.get_object(Bucket=bucket_name, Key=key)
    assert object_response['Body'].read().decode() == body

def test_video2audio(s3, bucket_name='syndicateapp', file_name='sample', file_ext='mp4'):
  with s3_bucket(s3, bucket_name):
    f = open(f"tests/data/{file_name}.{file_ext}", 'rb')
    s3.put_object(Bucket=bucket_name, Key=f"origin/{file_name}.{file_ext}", Body=f.read())
    f.close()
    event = {
      'Records': [
        {
          's3': {
            'bucket': {'name': bucket_name},
            'object': {'key': f"origin/{file_name}.{file_ext}", 'presigned_url': f"tests/data/{file_name}.{file_ext}"}
          }
        }
      ]
    }
    app.lambda_handler(event, {})
    audio_object=s3.get_object(Bucket=bucket_name, Key=f"audios/{file_name}.flac")
    data = bytearray(audio_object['Body'].read())
    assert data
    file = open(f"tests/data/{file_name}.flac", "wb")
    file.write(data)
    file.close()
    