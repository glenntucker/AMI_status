package main

import (
	"encoding/csv"
	"log"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/autoscaling"
	"github.com/aws/aws-sdk-go/service/ec2"
)

func main() {
	// Create a new AWS session
	sess := session.Must(session.NewSessionWithOptions(session.Options{
		SharedConfigState: session.SharedConfigEnable,
	}))

	// Create Auto Scaling and EC2 service clients
	asgSvc := autoscaling.New(sess)
	ec2Svc := ec2.New(sess)

	// Retrieve a list of Auto Scaling Groups
	asgInput := &autoscaling.DescribeAutoScalingGroupsInput{}
	asgResult, err := asgSvc.DescribeAutoScalingGroups(asgInput)
	if err != nil {
		log.Fatal("Failed to retrieve Auto Scaling Groups:", err)
	}

	// Create a CSV file to store the report
	file, err := os.Create("report.csv")
	if err != nil {
		log.Fatal("Failed to create report file:", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header row to the CSV file
	header := []string{"Auto Scaling Group", "Instance Count", "AMI ID", "AMI Creation Date"}
	err = writer.Write(header)
	if err != nil {
		log.Fatal("Failed to write CSV header:", err)
	}

	// Iterate through the Auto Scaling Groups
	for _, asg := range asgResult.AutoScalingGroups {
		groupName := aws.StringValue(asg.AutoScalingGroupName)

		// Retrieve information about instances in the Auto Scaling Group
		var instanceIDs []*string
		for _, instance := range asg.Instances {
			instanceIDs = append(instanceIDs, instance.InstanceId)
		}

		instInput := &autoscaling.DescribeAutoScalingInstancesInput{
			InstanceIds: instanceIDs,
		}
		instResult, err := asgSvc.DescribeAutoScalingInstances(instInput)
		if err != nil {
			log.Printf("Failed to retrieve instances for Auto Scaling Group %s: %v\n", groupName, err)
			continue
		}

		instanceCount := len(instResult.AutoScalingInstances)

		// Check if MixedInstancesPolicy and LaunchTemplate are specified for the Auto Scaling Group
		if asg.MixedInstancesPolicy != nil && asg.MixedInstancesPolicy.LaunchTemplate != nil {
			launchTemplateName := aws.StringValue(asg.MixedInstancesPolicy.LaunchTemplate.LaunchTemplateSpecification.LaunchTemplateName)
			launchTemplateVersion := aws.StringValue(asg.MixedInstancesPolicy.LaunchTemplate.LaunchTemplateSpecification.Version)

			// Retrieve AMI ID from the launch template
			ltInput := &ec2.DescribeLaunchTemplateVersionsInput{
				LaunchTemplateName: aws.String(launchTemplateName),
				Versions:           []*string{aws.String(launchTemplateVersion)},
			}
			ltResult, err := ec2Svc.DescribeLaunchTemplateVersions(ltInput)
			if err != nil {
				log.Printf("Failed to retrieve launch template for Auto Scaling Group %s: %v\n", groupName, err)
				continue
			}

			if len(ltResult.LaunchTemplateVersions) == 0 {
				log.Printf("No Launch Template found for Auto Scaling Group %s\n", groupName)
				continue
			}

			amiID := aws.StringValue(ltResult.LaunchTemplateVersions[0].LaunchTemplateData.ImageId)

			// Retrieve AMI creation date
			amiInput := &ec2.DescribeImagesInput{
				ImageIds: []*string{aws.String(amiID)},
			}
			amiResult, err := ec2Svc.DescribeImages(amiInput)
			if err != nil {
				log.Printf("Failed to retrieve AMI information for Auto Scaling Group %s: %v\n", groupName, err)
				continue
			}

			if len(amiResult.Images) == 0 {
				log.Printf("No AMIs found for Auto Scaling Group %s\n", groupName)
				continue
			}

			amiCreationDate := aws.StringValue(amiResult.Images[0].CreationDate)

			// Write the Auto Scaling Group summary to the CSV file
			record := []string{groupName, string(instanceCount), amiID, amiCreationDate}
			err = writer.Write(record)
			if err != nil {
				log.Printf("Failed to write Auto Scaling Group %s record to CSV: %v\n", groupName, err)
				continue
			}
		} else {
			log.Printf("No Launch Template specified for Auto Scaling Group %s\n", groupName)
			continue
		}
	}

	log.Println("Report generated successfully.")
}
