FROM public.ecr.aws/lambda/python:3.7
COPY ./numdevfun/app.py ${LAMBDA_TASK_ROOT}
COPY ./numdevfun/requirements.txt ./
# COPY ./numdevfun/whls ./whls
COPY ./numdevfun/lib ${LAMBDA_TASK_ROOT}/lib
RUN python -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
CMD ["app.handler"]