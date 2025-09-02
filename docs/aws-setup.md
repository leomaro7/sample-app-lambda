# AWS IAM Setup for GitHub Actions

This document describes how to set up AWS IAM roles and policies to enable GitHub Actions to deploy Lambda functions using OIDC (OpenID Connect) authentication.

## Prerequisites

- AWS CLI installed and configured with administrator access
- GitHub repository created

## Step 1: Create GitHub OIDC Identity Provider

Create an OIDC identity provider in AWS IAM:

```bash
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --thumbprint-list 1c58a3a8518e8759bf075b76b750d4f2df264fcd
```

## Step 2: Create IAM Policy for Lambda Deployment

Create a policy file `lambda-deploy-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaFunctionAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:GetFunction",
                "lambda:CreateFunction",
                "lambda:TagResource",
                "lambda:UntagResource",
                "lambda:ListTags",
                "lambda:PublishVersion",
                "lambda:GetFunctionConfiguration"
            ],
            "Resource": "arn:aws:lambda:*:*:function:*"
        },
        {
            "Sid": "IAMRoleAccess",
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "arn:aws:iam::*:role/lambda-execution-role*"
        },
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-lambda-deployment-bucket/*"
            ]
        },
        {
            "Sid": "LogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

Create the policy:

```bash
aws iam create-policy \
    --policy-name GitHubActionsLambdaDeployPolicy \
    --policy-document file://lambda-deploy-policy.json
```

## Step 3: Create IAM Role for GitHub Actions

Create a trust policy file `github-actions-trust-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
                }
            }
        }
    ]
}
```

**Important**: Replace `YOUR_ACCOUNT_ID`, `YOUR_GITHUB_USERNAME`, and `YOUR_REPO_NAME` with your actual values.

Create the role:

```bash
aws iam create-role \
    --role-name GitHubActionsRole \
    --assume-role-policy-document file://github-actions-trust-policy.json
```

## Step 4: Attach Policy to Role

Attach the policy to the role:

```bash
aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/GitHubActionsLambdaDeployPolicy
```

## Step 5: Create Lambda Execution Role

Create a Lambda execution role trust policy `lambda-trust-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Create the Lambda execution role:

```bash
aws iam create-role \
    --role-name lambda-execution-role \
    --assume-role-policy-document file://lambda-trust-policy.json

# Attach basic execution policy
aws iam attach-role-policy \
    --role-name lambda-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## Step 6: Create Lambda Function

Create your Lambda function (if it doesn't exist):

```bash
aws lambda create-function \
    --function-name sample-lambda-function \
    --runtime python3.13 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --description "Sample Lambda function for GitHub Actions deployment" \
    --timeout 30 \
    --memory-size 128
```

## Step 7: Set GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions, and add these secrets:

1. **AWS_ROLE_ARN**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole`
2. **LAMBDA_FUNCTION_NAME**: `sample-lambda-function`

## Step 8: (Optional) Create S3 Bucket for Large Deployments

If your Lambda package is larger than 50MB:

```bash
aws s3 mb s3://your-lambda-deployment-bucket-UNIQUE_SUFFIX
```

Then add this secret to GitHub:
- **S3_BUCKET**: `your-lambda-deployment-bucket-UNIQUE_SUFFIX`

## Verification

To verify your setup:

1. Check that the OIDC provider exists:
```bash
aws iam list-open-id-connect-providers
```

2. Check that the role exists:
```bash
aws iam get-role --role-name GitHubActionsRole
```

3. Check that the Lambda function exists:
```bash
aws lambda get-function --function-name sample-lambda-function
```

## Security Best Practices

1. **Principle of Least Privilege**: The IAM policies provided grant only the minimum permissions needed for Lambda deployment.

2. **Repository-Specific Access**: The trust policy restricts access to your specific GitHub repository.

3. **Use OIDC**: This setup uses OIDC instead of long-lived access keys, which is more secure.

4. **Regular Review**: Periodically review and update IAM policies and roles.

## Troubleshooting

### Common Issues:

1. **"AssumeRoleWithWebIdentity is not authorized"**
   - Verify the OIDC provider is created correctly
   - Check the trust policy has the correct GitHub repository path
   - Ensure the GitHub repository is public or the organization allows OIDC

2. **"Function not found"**
   - Verify the Lambda function exists in the specified region
   - Check the function name matches the GitHub secret

3. **"Access Denied" during deployment**
   - Review IAM policies and ensure all necessary permissions are granted
   - Check that the Lambda execution role exists and has proper permissions

For more information, see the [AWS documentation on using OIDC with GitHub Actions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html).