terraform {
  required_version = ">= 1.4.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = "eu-west-1" }

# CHEAP baseline: tiny instance only (no volumes, no S3)
resource "aws_instance" "demo" {
  ami           = "ami-12345678"   # placeholder; not applied
  instance_type = "t3.micro"       # very cheap
  tags = { Name = "DemoInstance" }
}
