# syndicate-backend

## Prerequisite

### Install aws cli

```bash
sudo apt install awscli
```

### Install aws sam cli

1. Download the [AWS SAM CLI.zip file](https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip) to a directory of your choice.

```bash
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
```

2. Verify the integrity and authenticity of the downloaded installer files by generating a hash value using the following command:

```bash
sha256sum aws-sam-cli-linux-x86_64.zip
```

The output should look like the following example:

```
 <64-character SHA256 hash value> aws-sam-cli-linux-x86_64.zip
```

Compare the 64-character SHA-256 hash value with the one for your desired AWS SAM CLI version in the [AWS SAM CLI release notes](https://github.com/aws/aws-sam-cli/releases/latest) on GitHub.

3. Unzip the installation files into the `sam-installation/` subdirectory.

```bash
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
```

4. Install the AWS SAM CLI.

```bash
sudo ./sam-installation/install
```

5. Verify the installation.

```bash
sam --version
```

### Install docker

Please follow [this](https://docs.docker.com/engine/install/ubuntu/).

## How to configure

### Google Application Credentials

Copy and paste google application json credentials file named `credentials.json` inside serverless dir:

```
export GOOGLE_APPLICATION_CREDENTIALS=credentials.json
export AWS_DEFAULT_REGION=us-east-1
```

## How to run

In addition to integrating with AWS Toolkits, you can also run AWS SAM in "debug mode" to attach to third-party debuggers like [ptvsd](https://pypi.org/project/ptvsd/) or [delve](https://github.com/go-delve/delve).

To run AWS SAM in debug mode, use commands [sam local invoke](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-invoke.html) or [sam local start-api](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html) with the --debug-port or -d option.

For example:

```bash
# Invoke a function locally in debug mode on port 5858
sam local invoke -d 5858 <function logical id>

# Start local API Gateway in debug mode on port 5858
sam local start-api -d 5858
```

# How to pass unit test

```
pip install -r tests/requirements.txt --user
python3 -m pytest tests/unit -v
```

## How to deploy

```bash
sam build
sam deploy --guided
```
