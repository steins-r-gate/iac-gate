###############################################################################
# DEMO ONLY — Static analysis for CI gate (no creds, do NOT apply in real env)
###############################################################################

terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

# --- SECURITY MISCONFIGS (on purpose) ----------------------------------------

resource "aws_s3_bucket" "demo" {
  bucket = "rs-demo-bucket-example-123456"
}

resource "aws_s3_bucket_public_access_block" "demo" {
  bucket                  = aws_s3_bucket.demo.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "public" {
  bucket = aws_s3_bucket.demo.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Sid       = "PublicRead",
      Effect    = "Allow",
      Principal = "*",
      Action    = ["s3:GetObject"],
      Resource  = ["${aws_s3_bucket.demo.arn}/*"]
    }]
  })
}

resource "aws_s3_bucket_acl" "public_acl" {
  bucket = aws_s3_bucket.demo.id
  acl    = "public-read"
}

# --- COST SIGNALS ------------------------------------------------------------

resource "aws_instance" "demo" {
  ami           = "ami-12345678"
  instance_type = "m5.4xlarge"     # way more expensive than t3.micro
  tags = { Name = "DemoInstance" }
}

resource "aws_ebs_volume" "cost_demo" {
  availability_zone = "eu-west-1a"
  size              = 500
  type              = "gp3"
  iops              = 3000
  throughput        = 125
  tags = { Name = "CostDemoVolume" }
}
