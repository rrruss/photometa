provider "aws" {
  profile = "default"
  region  = "us-west-2"
}


data "aws_ami" "amazon-linux-2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}


resource "aws_instance" "reddit" {
  ami                         = data.aws_ami.amazon-linux-2.id
  instance_type               = "t2.medium"
  key_name                    = "flaskDeployment1.pem"
  associate_public_ip_address = true
  security_groups             = ["ssh_inbound_only"]
  iam_instance_profile        = "ECR_readonly"
  user_data                   = file("user_data.sh")

  root_block_device {
    delete_on_termination = true
    volume_size           = 32
    volume_type           = "standard"
  }

  tags = {
    application = "reddit title location bot"
  }
}


output "instance_public_dns" {
  value = aws_instance.reddit.public_dns
}
