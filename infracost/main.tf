###############################################################################
# DEMO ONLY — Static analysis for CI gate (no creds, do NOT apply in real env)
# Purpose: trigger Checkov HIGH/CRITICAL and produce a clear Infracost delta.
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

# Provider only sets a region for pricing. We never apply in this demo.
provider "aws" {
  region = "eu-west-1"
}

# --- SECURITY MISCONFIGS (on purpose) ----------------------------------------

# 1) S3 bucket without server-side encryption (SSE) — bad on purpose
resource "aws_s3_bucket" "demo" {
  bucket = "rs-demo-bucket-example-123456" # must be globally unique if ever applied
}

# 2) Disable Block Public Access — bad on purpose
resource "aws_s3_bucket_public_access_block" "demo" {
  bucket                  = aws_s3_bucket.demo.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# 3) Public bucket policy — bad on purpose
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

# 4) Legacy public ACL — bad on purpose (expect deprecation warnings; that’s fine)
resource "aws_s3_bucket_acl" "public_acl" {
  bucket = aws_s3_bucket.demo.id
  acl    = "public-read"
}

# --- COST SIGNALS (so Infracost shows a non-zero delta) ----------------------

# A) Upsized EC2 instance (clear monthly cost)
resource "aws_instance" "demo" {
  ami           = "ami-12345678"   # placeholder; we are NOT applying
  instance_type = "m5.4xlarge"     # bigger than baseline t3.micro
  tags = { Name = "DemoInstance" }
}

# B) Large gp3 EBS volume (obvious additional monthly cost)
resource "aws_ebs_volume" "cost_demo" {
  availability_zone = "eu-west-1a"
  size              = 500           # GB
  type              = "gp3"
  iops              = 3000
  throughput        = 125
  tags = { Name = "CostDemoVolume" }
}
