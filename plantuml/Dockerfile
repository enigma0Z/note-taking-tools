FROM plantuml/plantuml-server:jetty

RUN cd webapps \
    && mkdir ROOT && cd ROOT \
    && unzip ../ROOT.war \
    && rm ../ROOT.war

COPY *.jar webapps/ROOT/WEB-INF/lib/
