import csv
import boto3
from collections import defaultdict

# Create AWS clients for Auto Scaling and EC2
asg_client = boto3.client('autoscaling')
ec2_client = boto3.client('ec2')

# Retrieve a list of Auto Scaling Groups
asg_response = asg_client.describe_auto_scaling_groups()
asg_groups = asg_response['AutoScalingGroups']

# Create a dictionary to store the instance count and creation date for each AMI ID
ami_info = defaultdict(lambda: {'count': 0, 'creation_date': ''})

# Iterate through the Auto Scaling Groups
for asg in asg_groups:
    launch_template_name = None
    launch_template_version = None

    # Check if LaunchTemplate is specified for the Auto Scaling Group
    if 'LaunchTemplate' in asg:
        launch_template = asg['LaunchTemplate']
        launch_template_name = launch_template['LaunchTemplateName']
        launch_template_version = launch_template['Version']

    if launch_template_name and launch_template_version:
        # Retrieve AMI ID from the launch template
        lt_response = ec2_client.describe_launch_template_versions(
            LaunchTemplateName=launch_template_name,
            Versions=[launch_template_version]
        )
        launch_template_versions = lt_response['LaunchTemplateVersions']

        if launch_template_versions:
            ami_id = launch_template_versions[0]['LaunchTemplateData']['ImageId']

            # Increment the instance count for the corresponding AMI ID
            ami_info[ami_id]['count'] += len(asg['Instances'])

            # Check if the creation date for the AMI is already retrieved
            if not ami_info[ami_id]['creation_date']:
                ami_response = ec2_client.describe_images(ImageIds=[ami_id])
                ami_info[ami_id]['creation_date'] = ami_response['Images'][0]['CreationDate']

# Create a CSV file to store the report
with open('count2.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header row to the CSV file
    header = ["AMI ID", "Instance Count", "Creation Date"]
    writer.writerow(header)

    # Write each AMI instance count and creation date to the CSV file
    for ami_id, info in ami_info.items():
        row = [ami_id, info['count'], info['creation_date']]
        writer.writerow(row)

print("Report generated successfully.")
