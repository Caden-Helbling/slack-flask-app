import boto3
import datetime

# Initialize AWS services
ec2_client = boto3.client('ec2')
sns_client = boto3.client('sns')

# Define the SNS topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-west-2:642957184755:sde-ec2-control'

def lambda_handler(event, context):
    # Get the current time in UTC
    current_time = datetime.datetime.utcnow()
    print(f"Current time: {current_time}")

    # Only proceed if it's 6 PM UTC
    if current_time.hour != 0:
        return {
            'statusCode': 200,
            'body': 'Not the scheduled time for execution.'
        }

    # Get all EC2 instances with the 'sde-ec2-control=true' tag
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'tag:sde-ec2-control', 'Values': ['true']}
        ]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            tags = instance.get('Tags', [])

            # Check if the "hold true" tag is present
            hold_true_tag = any(tag['Key'] == 'hold' and tag['Value'] == 'true' for tag in tags)
            
            if hold_true_tag:
                # Send an alert if "hold true" tag is found
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=f"A hold is active. Do you want to disable it with `/sdeec2control remove hold`?"
                )
            else:
                # Shut down the instance if the "hold true" tag is absent
                ec2_client.stop_instances(InstanceIds=[instance_id])
                print(f"Shutting down instance {instance_id}.")

    return {
        'statusCode': 200,
        'body': 'Lambda function executed successfully.'
    }
