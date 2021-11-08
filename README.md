# discord-bot

To run locally:

```
# one time setup
mkdir dynamo
cd dynamo
curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
tar zxvf dynamo_db_local_latest.tar.gz

# to run dynamodb
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb &

# to create bot table / insert test records
# note: verify/update IDs/channel names in local_setup.py before running
python local_setup.py

# to run the bot
python main.py local
```

```pip install discord pyyaml boto3```

```python main.py```

Better instructions/documentation might be here someday.