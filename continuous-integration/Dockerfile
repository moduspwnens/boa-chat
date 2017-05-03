FROM amazonlinux:latest

RUN yum -y groupinstall "Development Tools"
RUN yum install -y python27-devel python35-devel gcc findutils zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel
RUN curl https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tar.xz -o python.tar.xz && tar xf python.tar.xz
RUN cd Python* && ./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
RUN cd Python* && make
RUN cd Python* && make altinstall && cd .. && rm -rf Python*
RUN curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && rm -f get-pip.py
RUN pip install virtualenv
RUN curl --silent --location https://rpm.nodesource.com/setup_6.x | bash - && yum install -y nodejs
RUN npm install -g grunt grunt-cli gulp bower
RUN virtualenv /venv
RUN python3.6 -m venv /venv3
RUN mkdir -p /project-source/boa-nimbus && mkdir -p /project-source/
COPY boa-nimbus/ /project-source/boa-nimbus/
COPY scripts/ /project-source/scripts/
RUN virtualenv /cache-venv && \
  cd /project-source/ && \
  pip install git+git://github.com/moduspwnens/boa-nimbus.git && \
  pip install scripts/preprocess-swagger-input && \
  find /project-source -name 'requirements.txt' | while read -r EACH_PATH ; do /cache-venv/bin/pip install -r "$EACH_PATH"; done && \
  rm -rf /cache-venv