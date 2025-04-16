# EC2 Instance Control via Slack - User Guide

This guide explains how to use our custom Slack slash command to control AWS EC2 instances directly from Slack.

## Overview

Our custom Slack command allows designated team members to control SDE Test EC2 instances directly from a specific Slack channel. This eliminates the need to log into the AWS console for routine instance management tasks.

## Available Commands

The following commands are available for managing EC2 instances:

| Command | Description |
|---------|-------------|
| `turn on` | Start all stopped SDE Test instances |
| `initiate hold` | Mark instances with a hold tag (prevents automatic shutdown) |
| `remove hold` | Remove the hold tag from instances (allows automatic shutdown) |

## How to Use the Commands

### Basic Usage

1. Make sure you are in the designated Slack channel where the command is authorized to work.
2. Type the slash command followed by one of the available commands:
   ```
   /sdeec2control turn on
   ```
   ```
   /sdeec2control initiate hold
   ```
   ```
   /sdeec2control remove hold
   ```

### Command Details

#### Turn On Instances
```
/sdeec2control turn on
```
This command will start all SDE Test instances that are currently in a stopped state. If all instances are already running, you'll receive a notification that instances are already on.

#### Initiate Hold
```
/sdeec2control initiate hold
```
This command tags the SDE Test instances with `hold=true`, which prevents them from being automatically shut down by cost-saving scripts or policies. Use this when you need instances to remain running for an extended period.

#### Remove Hold
```
/sdeec2control remove hold
```
This command changes the tag to `hold=false`, allowing automatic shutdown scripts to turn off the instances when needed. Use this when you no longer need the instances to stay running.

## Permissions and Access

- This slash command will only work in the designated Slack channel
- If you try to use it in another channel, you'll receive a message saying the command can only be used in a specific channel
- Contact your administrator if you need access to use these commands

## Response Types

After executing a command, you'll see a response in the channel that confirms the action:
- When starting instances: "Started SDE Test instances."
- When initiating a hold: "Initiated hold on SDE Test instances."
- When removing a hold: "Removed hold on SDE Test instances."
- If instances are already running: "SDE Test instances are already on."
- If no matching instances are found: "No instances found."

## Best Practices

1. **Communicate with your team**: Before turning on instances or changing hold status, let others in the channel know what you're doing
2. **Remove hold when done**: To save costs, remember to remove the hold when extended runtime is no longer needed
3. **Check responses**: Always check the response to ensure your command was processed successfully

## Troubleshooting

If you encounter issues:

1. **Command not recognized**: Make sure you're typing one of the exact commands listed above
2. **No response**: The server might be temporarily unavailable or you might not have the necessary AWS permissions
3. **"No instances found"**: This means no instances with the required tags were found in the AWS account

## Support

If you need assistance with the slash command:

1. Contact your DevOps or Cloud team
2. Refer to this documentation for command syntax
3. Check the AWS console to verify instance status if commands aren't working as expected