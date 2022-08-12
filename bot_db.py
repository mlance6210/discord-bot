import boto3
import yaml
from boto3.dynamodb.conditions import Key

def environment():
    from sys import argv
    if len(argv) > 1 and argv[1] == "local":
        return "local"
    return "prod"


env = environment()


def dynamodb_client():
    from sys import argv
    if env == "local":
        return boto3.resource("dynamodb", region_name="us-east-2",
                              endpoint_url="http://localhost:8000",
                              aws_secret_access_key="fake", aws_access_key_id="fake")

    return boto3.resource("dynamodb", "us-west-1")


dynamodb = dynamodb_client()


def get_message(guild_id):
    table = dynamodb.Table('betabot')
    response = table.query(
        KeyConditionExpression=Key('id').eq(str(guild_id) + ".msg"))
    return response["Items"][0]["value"]


def get_config(guild_id):
    table = dynamodb.Table('betabot')
    response = table.query(
        KeyConditionExpression=Key('id').eq(str(guild_id) + ".yaml"))
    return yaml.safe_load(response["Items"][0]["value"])


def get_token():
    if env == "local":
        with open("token_test.txt", "r") as f:
            return f.readline()
    table = dynamodb.Table('betabot')
    response = table.query(
        KeyConditionExpression=Key('id').eq("token"))
    return response["Items"][0]["value"]
