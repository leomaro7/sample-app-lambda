# GitHub Actions 用 AWS IAM セットアップ

この文書では、OIDC（OpenID Connect）認証を使用してGitHub ActionsがLambda関数をデプロイできるようにするためのAWS IAMロールとポリシーの設定方法について説明します。

## 前提条件

- AWS CLIがインストールされ、管理者アクセスで設定されている
- GitHubリポジトリが作成されている

## ステップ 1: GitHub OIDC アイデンティティプロバイダーの作成

AWS IAMでOIDCアイデンティティプロバイダーを作成します：

```bash
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --thumbprint-list 1c58a3a8518e8759bf075b76b750d4f2df264fcd
```

## ステップ 2: Lambda デプロイ用 IAM ポリシーの作成

ポリシーファイル `lambda-deploy-policy.json` を作成します：

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

ポリシーを作成します：

```bash
aws iam create-policy \
    --policy-name GitHubActionsLambdaDeployPolicy \
    --policy-document file://lambda-deploy-policy.json
```

## ステップ 3: GitHub Actions 用 IAM ロールの作成

信頼ポリシーファイル `github-actions-trust-policy.json` を作成します：

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

**重要**: `YOUR_ACCOUNT_ID`、`YOUR_GITHUB_USERNAME`、`YOUR_REPO_NAME` を実際の値に置き換えてください。

ロールを作成します：

```bash
aws iam create-role \
    --role-name GitHubActionsRole \
    --assume-role-policy-document file://github-actions-trust-policy.json
```

## ステップ 4: ポリシーをロールにアタッチ

ポリシーをロールにアタッチします：

```bash
aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/GitHubActionsLambdaDeployPolicy
```

## ステップ 5: Lambda 実行ロールの作成

Lambda実行ロール用の信頼ポリシー `lambda-trust-policy.json` を作成します：

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

Lambda実行ロールを作成します：

```bash
aws iam create-role \
    --role-name lambda-execution-role \
    --assume-role-policy-document file://lambda-trust-policy.json

# 基本実行ポリシーをアタッチ
aws iam attach-role-policy \
    --role-name lambda-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## ステップ 6: Lambda 関数の作成

Lambda関数を作成します（まだ存在しない場合）：

```bash
aws lambda create-function \
    --function-name sample-lambda-function \
    --runtime python3.13 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --description "GitHub Actions デプロイ用のサンプル Lambda 関数" \
    --timeout 30 \
    --memory-size 128
```

## ステップ 7: GitHub シークレットの設定

GitHubリポジトリで、Settings > Secrets and variables > Actions に移動し、以下のシークレットを追加します：

1. **AWS_ROLE_ARN**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole`
2. **LAMBDA_FUNCTION_NAME**: `sample-lambda-function`

## ステップ 8: （オプション）大容量デプロイ用 S3 バケットの作成

Lambdaパッケージが50MBより大きい場合：

```bash
aws s3 mb s3://your-lambda-deployment-bucket-UNIQUE_SUFFIX
```

その後、GitHubに以下のシークレットを追加します：
- **S3_BUCKET**: `your-lambda-deployment-bucket-UNIQUE_SUFFIX`

## 検証

設定を検証するには：

1. OIDCプロバイダーが存在することを確認：
```bash
aws iam list-open-id-connect-providers
```

2. ロールが存在することを確認：
```bash
aws iam get-role --role-name GitHubActionsRole
```

3. Lambda関数が存在することを確認：
```bash
aws lambda get-function --function-name sample-lambda-function
```

## セキュリティのベストプラクティス

1. **最小権限の原則**: 提供されるIAMポリシーは、Lambdaデプロイに必要な最小限の権限のみを付与します。

2. **リポジトリ固有のアクセス**: 信頼ポリシーは、特定のGitHubリポジトリへのアクセスを制限します。

3. **OIDCの使用**: この設定では、長期間有効なアクセスキーの代わりにOIDCを使用するため、より安全です。

4. **定期的な見直し**: IAMポリシーとロールを定期的に見直し、更新してください。

## トラブルシューティング

### よくある問題:

1. **"AssumeRoleWithWebIdentity is not authorized"**
   - OIDCプロバイダーが正しく作成されているか確認
   - 信頼ポリシーに正しいGitHubリポジトリパスが含まれているか確認
   - GitHubリポジトリがパブリックであるか、組織がOIDCを許可しているか確認

2. **"Function not found"**
   - 指定したリージョンにLambda関数が存在するか確認
   - 関数名がGitHubシークレットと一致しているか確認

3. **デプロイ中の"Access Denied"**
   - IAMポリシーを確認し、必要な権限がすべて付与されているか確認
   - Lambda実行ロールが存在し、適切な権限を持っているか確認

詳細については、[GitHub ActionsでOIDCを使用するAWSドキュメント](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html)を参照してください。