FROM public.ecr.aws/lambda/python:3.7
COPY ./testtestnumdevfun/app.py ${LAMBDA_TASK_ROOT}
COPY ./testnumdevfun/requirements.txt ./
# COPY ./testnumdevfun/whls ./whls
COPY ./testnumdevfun/lib ${LAMBDA_TASK_ROOT}/lib
RUN python -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
CMD ["app.handler"]