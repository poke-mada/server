import os
from storages.backends.s3boto3 import S3Boto3Storage

ENVIRONMENT = os.getenv("DJANGO_ENV", "prod")  # "dev", "stage" o "prod"


class StaticsStorage(S3Boto3Storage):
    location = 'pokemon-statics'


class MediaStorage(S3Boto3Storage):
    location = f'{ENVIRONMENT}/dedsafio-pokemon/media'
