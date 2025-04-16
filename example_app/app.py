from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

# Replace this with your target Slack channel ID
ALLOWED_CHANNEL_ID = "C08AAHM3C8N"

def get_ec2_client():
    """Create EC2 client."""
    return boto3.client('ec2', region_name='us-west-2')

@app.route("/", methods=["POST"])
def control_instances():
    data = request.form  # Handle form data from Slack
    channel_id = data.get("channel_id")  # Get the channel ID from the request
    
    # Check if the request is coming from the allowed channel
    if channel_id != ALLOWED_CHANNEL_ID:
        response = {
            "response_type": "ephemeral",
            "text": "This command can only be used in a specific channel."
        }
        return jsonify(response)

    message = data.get("text", "").lower()
    tag_key = "sde-ec2-control"
    tag_value = "true"
    ec2_client = get_ec2_client()

    if "turn on" in message:
        # Command: Turn on instances
        instances = ec2_client.describe_instances(
            Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}, {'Name': 'instance-state-name', 'Values': ['stopped']}]
        )
        instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
        if not instance_ids:
            return jsonify({"response_type": "in_channel", "text": "SDE Test instances are already on."})
        ec2_client.start_instances(InstanceIds=instance_ids)
        return jsonify({"response_type": "in_channel", "text": f"Started SDE Test instances."})

    elif "initiate hold" in message:
        # Command: Initiate hold (tag instances with hold=true)
        hold = "true"
        instances = ec2_client.describe_instances(
            Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
        )
        instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
        if not instance_ids:
            return jsonify({"response_type": "in_channel", "text": "No instances found."})
        ec2_client.create_tags(Resources=instance_ids, Tags=[{'Key': 'hold', 'Value': hold}])
        return jsonify({"response_type": "in_channel", "text": f"Initiated hold on SDE Test instances."})

    elif "remove hold" in message:
        # Command: Remove hold (tag instances with hold=false)
        hold = "false"
        instances = ec2_client.describe_instances(
            Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
        )
        instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
        if not instance_ids:
            return jsonify({"response_type": "in_channel", "text": "No instances found."})
        ec2_client.create_tags(Resources=instance_ids, Tags=[{'Key': 'hold', 'Value': hold}])
        return jsonify({"response_type": "in_channel", "text": f"Removed hold on SDE Test instances."})

    else:
        return jsonify({"response_type": "in_channel", "text": "Unrecognized command. Use 'turn on', 'initiate hold', or 'remove hold'."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
