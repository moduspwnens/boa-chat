FROM amazonlinux:latest

RUN curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && rm -f get-pip.py
RUN pip install virtualenv
RUN yum -y groupinstall "Development Tools" ; yum clean all
RUN yum install -y python27-devel gcc findutils ; yum clean all
RUN virtualenv /venv
RUN mkdir -p /project-source/boa-nimbus && mkdir -p /project-source/
COPY boa-nimbus/ /project-source/boa-nimbus/
COPY scripts/ /project-source/scripts/
RUN virtualenv /cache-venv && \
  cd /project-source/ && \
  ls -la && \
  find /project-source -name 'requirements.txt' | while read -r EACH_PATH ; do /cache-venv/bin/pip install -r "$EACH_PATH"; done && \
  rm -rf /cache-venv