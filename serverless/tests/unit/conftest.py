import pytest
import os
import boto3

from moto import mock_s3

pytest.aws_region = 'us-east-1'

@pytest.fixture(scope='function')
def aws_credentials():
  os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
  os.environ['AWS_SECRET_ACCESS_ID'] = 'testing'
  os.environ['AWS_SECURITY_TOKEN'] = 'testing'
  os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def s3(aws_credentials):
  with mock_s3():
    yield boto3.client('s3', region_name=pytest.aws_region)
    