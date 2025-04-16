import json
import boto3
import urllib.parse

def get_ec2_client():
    """Create EC2 client using Lambda's IAM role."""
    return boto3.client('ec2', region_name='us-west-2')

def process_instances(ec2_client, tag_key, tag_value, action, message):
    """Process EC2 instances based on tags and action."""
    # Get instances with the specified tag
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            }
        ]
    )
    
    # Collect instance IDs
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    
    if not instance_ids:
        return 'No instances found with the specified tag.'
    
    # Perform the requested action
    if action == 'tag':
        keep_working = 'true' if 'keep-working' in message else 'false'
        ec2_client.create_tags(
            Resources=instance_ids,
            Tags=[
                {'Key': 'keep-working', 'Value': keep_working}
            ]
        )
        return f"Tagged {len(instance_ids)} instances with keep-working: {keep_working}"
        
    elif action == 'start':
        # Filter for stopped instances
        stopped_response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': f'tag:{tag_key}',
                    'Values': [tag_value]
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['stopped']
                }
            ]
        )
        
        # Collect stopped instance IDs
        stopped_instance_ids = []
        for reservation in stopped_response['Reservations']:
            for instance in reservation['Instances']:
                stopped_instance_ids.append(instance['InstanceId'])
        
        if not stopped_instance_ids:
            return 'No stopped instances found with the specified tag.'
        
        # Start the instances
        ec2_client.start_instances(InstanceIds=stopped_instance_ids)
        return f"Started {len(stopped_instance_ids)} instances"

def lambda_handler(event, context):
    try:
        # Parse the request body from Slack
        if 'body' in event:
            # Handle API Gateway request with content type application/x-www-form-urlencoded
            body = event['body']
            if event.get('isBase64Encoded', False):
                import base64
                body = base64.b64decode(body).decode('utf-8')
            
            # Parse the form data
            params = dict(urllib.parse.parse_qsl(body))
            message = params.get('text', '').lower()
        else:
            # Fallback if we can't find the expected format
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request format')
            }
        
        # Define the tag key and value for filtering instances
        tag_key = 'SDE-start'
        tag_value = 'true'
        
        # Create EC2 client
        ec2 = get_ec2_client()
        
        # Determine action based on message
        if 'keep-working' in message or 'stop-working' in message:
            action = 'tag'
        elif 'start' in message:
            action = 'start'
        else:
            return {
                'statusCode': 200,
                'body': json.dumps("Unrecognized command. Use 'start', 'keep-working', or 'stop-working'.")
            }
        
        # Process instances
        result = process_instances(ec2, tag_key, tag_value, action, message)
        
        # Format the response for Slack
        slack_response = {
            "response_type": "in_channel",  # Makes the response visible to all users in the channel
            "text": result
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(slack_response)
        }
    
    except Exception as e:
        print(f'Error: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }