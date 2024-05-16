FROM python:3.11-slim

WORKDIR /app

COPY . .

EXPOSE 8000

RUN pip install -r requirements_no_nlp.txt

#comment the above command and uncomment the below one to use our API with HuggingFace Models

#RUN pip install -r requirements_with_nlp.txt