import boto3

test_guild_id = 821375206626295847  # change for your test server
test_msg_key = str(test_guild_id) + ".msg"
test_config_key = str(test_guild_id) + ".yaml"

test_msg = "Hey $name. You missed $trial. That's your $no_show_ct no show."
test_config = \
    """#config
metadata:
  server:
    name: "Meow"
config:
  channel:
    id: 881172868514324540
  run_log_channel:
    name: "bot-posts-test"
"""

dynamodb = boto3.client("dynamodb", region_name="us-east-2",
                        endpoint_url="http://localhost:8000",
                        aws_secret_access_key="fake", aws_access_key_id="fake")


def create_bot_table():
    tables = dynamodb.list_tables()
    if 'TableNames' in tables:
        table_list = tables['TableNames']
        for table in table_list:
            if table == 'bot':
                return

    table = dynamodb.create_table(
        TableName='bot',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table


def put_msg():
    response = dynamodb.put_item(
        TableName='bot',
        Item={
            'id': {'S': test_msg_key},
            'value': {'S': test_msg}
        }
    )
    return response


def put_config():
    response = dynamodb.put_item(
        TableName='bot',
        Item={
            'id': {'S': test_config_key},
            'value': {'S': test_config}
        }
    )
    return response


if __name__ == "__main__":
    create_bot_table()
    put_config()
    put_msg()
