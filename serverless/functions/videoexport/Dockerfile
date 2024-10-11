FROM public.ecr.aws/lambda/python:3.8
RUN yum -y install unzip
COPY layers/fonts/* /usr/local/share/fonts/
COPY layers/ffmpeg/bin/* /usr/local/bin/
RUN chmod 777 -R /usr/local/bin/ffmpeg
RUN chmod 777 -R /usr/local/bin/ffprobe
COPY functions/videoexport/* ./
RUN python3 -m pip install -r requirements.txt
CMD ["app.lambda_handler"]
