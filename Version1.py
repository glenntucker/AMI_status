import csv
import boto3

# Create AWS clients for Auto Scaling and EC2
asg_client = boto3.client('autoscaling')
ec2_client = boto3.client('ec2')

# Retrieve a list of Auto Scaling Groups
asg_response = asg_client.describe_auto_scaling_groups()
asg_groups = asg_response['AutoScalingGroups']

# Create a CSV file to store the report
with open('report2.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header row to the CSV file
    header = ["Auto Scaling Group", "Instance Count", "AMI ID", "AMI Creation Date"]
    writer.writerow(header)

    # Iterate through the Auto Scaling Groups
    for asg in asg_groups:
        group_name = asg['AutoScalingGroupName']

        # Retrieve information about instances in the Auto Scaling Group
        instance_ids = [instance['InstanceId'] for instance in asg['Instances']]
        instance_count = len(instance_ids)

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

                # Retrieve AMI creation date
                ami_response = ec2_client.describe_images(ImageIds=[ami_id])
                ami_images = ami_response['Images']

                if ami_images:
                    ami_creation_date = ami_images[0]['CreationDate']

                    # Write the Auto Scaling Group summary to the CSV file
                    row = [group_name, str(instance_count), ami_id, ami_creation_date]
                    writer.writerow(row)
                else:
                    print(f"No AMIs found for Auto Scaling Group: {group_name}")
            else:
                print(f"No Launch Template found for Auto Scaling Group: {group_name}")
        else:
            print(f"No Launch Template specified for Auto Scaling Group: {group_name}")

print("Report generated successfully.")
