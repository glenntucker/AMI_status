import csv
import boto3
from collections import defaultdict

# Create AWS clients for Auto Scaling and EC2
asg_client = boto3.client('autoscaling')
ec2_client = boto3.client('ec2')

# Retrieve a list of Auto Scaling Groups
asg_response = asg_client.describe_auto_scaling_groups()
asg_groups = asg_response['AutoScalingGroups']

# Create a dictionary to store the instance count for each AMI ID
ami_instance_counts = defaultdict(int)

# Iterate through the Auto Scaling Groups
for asg in asg_groups:
    # Check if LaunchTemplate is specified for the Auto Scaling Group
    if 'MixedInstancesPolicy' in asg and 'LaunchTemplate' in asg['MixedInstancesPolicy']:
        launch_template = asg['MixedInstancesPolicy']['LaunchTemplate']['LaunchTemplateSpecification']
        launch_template_name = launch_template['LaunchTemplateName']
        launch_template_version = launch_template['Version']

        # Retrieve AMI ID from the launch template
        lt_response = ec2_client.describe_launch_template_versions(
            LaunchTemplateName=launch_template_name,
            Versions=[launch_template_version]
        )
        launch_template_versions = lt_response['LaunchTemplateVersions']

        if launch_template_versions:
            ami_id = launch_template_versions[0]['LaunchTemplateData']['ImageId']

            # Increment the instance count for the corresponding AMI ID
            ami_instance_counts[ami_id] += len(asg['Instances'])

# Create a CSV file to store the report
with open('report.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header row to the CSV file
    header = ["AMI ID", "Instance Count"]
    writer.writerow(header)

    # Write each AMI instance count to the CSV file
    for ami_id, count in ami_instance_counts.items():
        row = [ami_id, count]
        writer.writerow(row)

print("Report generated successfully.")
