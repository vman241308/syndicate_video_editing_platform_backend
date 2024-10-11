FROM public.ecr.aws/lambda/python:3.8
ARG credentials
ENV GOOGLE_APPLICATION_CREDENTIALS $credentials
COPY credentials.json $credentials
RUN chmod 777 -R $credentials
COPY functions/audio2srt/* ./
COPY layers/ffmpeg/bin/* /usr/local/bin/
RUN chmod 777 -R /usr/local/bin/ffmpeg
RUN chmod 777 -R /usr/local/bin/ffprobe
RUN python3 -m pip install -r requirements.txt
CMD ["app.lambda_handler"]
