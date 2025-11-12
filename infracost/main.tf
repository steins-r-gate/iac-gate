# Provider only sets a region for static analysis. No creds are used; we never apply.
provider "aws" {
  region = "eu-west-1"
}

# S3 bucket without server-side encryption (bad on purpose)
resource "aws_s3_bucket" "demo" {
  bucket = "rs-demo-bucket-example-123456"
}

# Disable Block Public Access and attach a public policy (bad on purpose)
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

# EC2 to produce a visible monthly cost signal
resource "aws_instance" "demo" {
  ami           = "ami-12345678"   # placeholder; we won't apply
  instance_type = "t3.large"
  tags = { Name = "DemoInstance" }
}
