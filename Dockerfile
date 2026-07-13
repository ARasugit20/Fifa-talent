FROM public.ecr.aws/lambda/python:3.11

COPY pyproject.toml README.md /var/task/
COPY src/ /var/task/src/

RUN pip install --no-cache-dir .

CMD ["india_football_funnel.aws.lambda_handlers.etl_handler"]
