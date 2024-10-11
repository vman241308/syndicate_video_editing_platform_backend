from functions.audio2srt import app
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

def test_audio2srt(s3, bucket_name='syndicateapp', file_name='sample'):
  with s3_bucket(s3, bucket_name):
    f = open(f"tests/data/{file_name}.flac", 'rb')
    s3.put_object(Bucket=bucket_name, Key=f"audios/{file_name}.flac", Body=f.read())
    f.close()
    event = {
      'Records': [
        {
          's3': {
            'bucket': {'name': bucket_name},
            'object': {'key': f"audios/{file_name}.flac", 'presigned_url': f"tests/data/{file_name}.flac"}
          }
        }
      ]
    }
    app.lambda_handler(event, {})
    subtitle_object=s3.get_object(Bucket=bucket_name, Key=f"subtitles/{file_name}.srt")
    data = subtitle_object['Body'].read()
    assert data
    with open(f"tests/data/{file_name}.srt", "wb") as file:
      file.write(data)
      file.close()
