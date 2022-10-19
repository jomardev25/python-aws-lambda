import boto3
import json
import logging
from decimal import Decimal
from custom_encoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamoTableName = 'products'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamoTableName)


def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    resource = event['resource']
    pathParameters = event['pathParameters']
    queryStringParameters = event['queryStringParameters']
    path = event['path']
    
    if httpMethod == 'GET' and path == '/health':
        response = buildResponse(200, 'Health check')
    elif httpMethod == 'GET' and path == '/products' and resource == "/products":
        response = getProducts()
    elif httpMethod == 'GET' and resource == '/products/{id}':
        response = getSingleProduct(pathParameters['id'])
    elif httpMethod == 'POST' and path == '/products':
        response = saveProduct(json.loads(event['body'], parse_float=Decimal))
    elif httpMethod == 'PATCH' and path == '/products':
        response = updateProduct(json.loads(event['body'], parse_float=Decimal))
    elif httpMethod == 'DELETE' and path == '/products':
        response = deleteProduct(queryStringParameters['id'])
    else:
       response = buildResponse(404, 'Not Found.')
 
    return response


def getProducts():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Items'])

        body = {
            'products': result
        }

        return buildResponse(200, response)

    except:
        logger.exception('Custom Logger here')


def getSingleProduct(id):
    response = table.get_item(Key={'id': int(id)})

    if 'Item' in response:
        return buildResponse(200, response['Item'])
    else:
        return buildResponse(404, {'message': 'Product Id: %s not found.' % id})


def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody,  ReturnValues='ALL_OLD')
        body = {
            'operation': 'SAVE',
            'message': 'success',
            'item': requestBody
        }
        return buildResponse(201, body)
    except:
        logger.exception('Custom Logger here')
        

def updateProduct(requestBody):
    try:
        response = table.update_item(
            Key={
                'id': int(requestBody['id'])
            },
            ConditionExpression= 'attribute_exists(id)',
            UpdateExpression='SET description = :description, price = :price',
            ExpressionAttributeValues={
                ':description': requestBody['description'],
                ':price': Decimal(requestBody['price'])
            },
            ReturnValues='UPDATED_NEW'
        )
        item = response['Attributes']
        item['id'] = int(requestBody['id'])
        return buildResponse(200, item)
    except:
        logger.exception('Custom Logger here')

def deleteProduct(id):
    try:
        response = table.delete_item(Key={'id': int(id)}, ReturnValues='ALL_OLD')
        body = {
                    'operation': 'DELETE',
                    'message': 'success',
                    'item': response
                }
        return buildResponse(200, response)
    except:
        logger.exception('Custom Logger here')


def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers':{
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)

    return response