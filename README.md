# AWS Lambda GitHub Actions デプロイメントサンプル

このリポジトリは、2025年8月に発表されたGitHub Actionsの新機能を使用してAWS Lambda関数を自動デプロイする方法を示しています。シンプルなPython Lambda関数と、GitHub Actionsによる自動テスト・デプロイメントが含まれています。

## 機能

- ✅ **Python 3.13 Lambda関数**: ヘルスチェックとグリーティングエンドポイントを持つシンプルなREST API
- ✅ **自動テスト**: pytestによるユニットテスト
- ✅ **GitHub Actions CI/CD**: mainブランチプッシュ時の自動デプロイ
- ✅ **Dry Run対応**: プルリクエスト時のデプロイメント検証
- ✅ **OIDC認証**: 長期間有効な認証情報を使わないセキュアなデプロイ
- ✅ **モダンPython**: タイムゾーン対応のdatetimeとPythonベストプラクティスに準拠

## アーキテクチャ

```
├── src/
│   └── lambda_function.py          # メインのLambda関数
├── tests/
│   ├── __init__.py
│   └── test_lambda_function.py     # ユニットテスト
├── .github/
│   └── workflows/
│       └── deploy-lambda.yml       # GitHub Actionsワークフロー
├── docs/
│   └── aws-setup.md               # 詳細なAWSセットアップガイド
├── requirements.txt               # Python依存関係
└── README.md                      # このファイル
```

## Lambda関数のエンドポイント

サンプルLambda関数は以下のREST APIエンドポイントを提供します：

- `GET /` - ヘルスチェックエンドポイント
- `GET /hello?name=<name>` - オプションのnameパラメータ付きグリーティングエンドポイント
- `POST /hello` - JSONボディ `{"name": "value"}` でのグリーティング作成

## クイックスタート

### 1. リポジトリをフォーク・クローン

```bash
git clone https://github.com/YOUR_USERNAME/sample-app-lambda.git
cd sample-app-lambda
```

### 2. AWSセットアップ（必須）

[`docs/aws-setup.md`](docs/aws-setup.md) の詳細なセットアップガイドに従って以下を実行してください：

1. GitHub OIDC Identity Providerの作成
2. IAMロールとポリシーの設定
3. Lambda関数の作成
4. GitHub Secretsの設定

**必要なGitHub Secrets:**
- `AWS_ROLE_ARN`: GitHub Actions用IAMロールのARN
- `LAMBDA_FUNCTION_NAME`: Lambda関数名

### 3. ローカルテスト

依存関係をインストールしてテストを実行：

```bash
# Python依存関係のインストール
pip install pytest boto3 moto

# テスト実行
python -m pytest tests/ -v
```

### 4. デプロイ

mainブランチにプッシュして自動デプロイを実行：

```bash
git add .
git commit -m "Initial Lambda function"
git push origin main
```

GitHub Actionsワークフローが以下を実行します：
- ユニットテストの実行
- デプロイメントパッケージのビルド
- AWS Lambdaへのデプロイ
- 関数設定（メモリ、タイムアウト、環境変数）の設定

## GitHub Actionsワークフロー

ワークフローには3つのジョブが含まれています：

### 1. テストジョブ
- すべてのプッシュとプルリクエストで実行
- Python 3.13のセットアップ
- 依存関係のインストール
- pytestユニットテストの実行

### 2. デプロイジョブ（mainブランチのみ）
- テスト成功後に実行
- AWS認証にOIDCを使用
- 本番構成でLambda関数をデプロイ
- 環境変数設定：`ENVIRONMENT=production`, `LOG_LEVEL=INFO`

### 3. Dry Runジョブ（プルリクエストのみ）
- 変更を加えずにデプロイメントを検証
- ステージング構成を使用
- 環境変数設定：`ENVIRONMENT=staging`, `LOG_LEVEL=DEBUG`

## 設定

### Lambda関数設定

GitHub Actionsデプロイメントでは以下を設定します：

- **ランタイム**: Python 3.13
- **ハンドラー**: `lambda_function.lambda_handler`
- **メモリ**: 128 MB
- **タイムアウト**: 30秒
- **説明**: "Sample Lambda function deployed via GitHub Actions"

### 環境変数

関数では以下の環境変数を使用します：

- `ENVIRONMENT`: "production" または "staging" に設定
- `LOG_LEVEL`: "INFO" または "DEBUG" に設定

## デプロイした関数のテスト

### AWS CLIを使用

```bash
# ヘルスチェックのテスト
aws lambda invoke \
  --function-name your-function-name \
  --payload '{"httpMethod":"GET","path":"/"}' \
  response.json && cat response.json

# グリーティングエンドポイントのテスト
aws lambda invoke \
  --function-name your-function-name \
  --payload '{"httpMethod":"GET","path":"/hello","queryStringParameters":{"name":"Alice"}}' \
  response.json && cat response.json
```

### API Gateway使用（設定した場合）

API Gateway統合を設定した場合：

```bash
# ヘルスチェック
curl https://your-api-id.execute-api.region.amazonaws.com/stage/

# グリーティング
curl https://your-api-id.execute-api.region.amazonaws.com/stage/hello?name=Alice

# グリーティング作成
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/stage/hello \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob"}'
```

## 開発ワークフロー

### 新機能の追加

1. フィーチャーブランチを作成：
   ```bash
   git checkout -b feature/new-endpoint
   ```

2. `src/lambda_function.py`に変更を追加
3. `tests/test_lambda_function.py`に対応するテストを追加
4. コミットとプッシュ：
   ```bash
   git add .
   git commit -m "Add new endpoint"
   git push origin feature/new-endpoint
   ```

5. プルリクエストを作成 - これによりDry Runデプロイメントが実行されます
6. レビュー後、mainにマージして本番デプロイメント

### ローカルでのテスト実行

```bash
# テスト依存関係のインストール
pip install pytest boto3 moto

# すべてのテストを実行
python -m pytest tests/ -v

# 特定のテストを実行
python -m pytest tests/test_lambda_function.py::TestLambdaFunction::test_health_check_endpoint -v

# カバレッジ付きで実行
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## トラブルシューティング

### よくある問題

1. **GitHub Actionsが"AssumeRoleWithWebIdentity is not authorized"エラーで失敗**
   - AWS IAMでOIDCプロバイダー設定を確認
   - 信頼ポリシーに正しいGitHubリポジトリパスがあることを確認
   - `AWS_ROLE_ARN` secretが正しく設定されていることを確認

2. **Lambdaデプロイが"Function not found"エラーで失敗**
   - まずLambda関数を手動で作成（aws-setup.mdを参照）
   - `LAMBDA_FUNCTION_NAME` secretが実際の関数名と一致することを確認
   - ワークフローのAWSリージョン設定を確認

3. **ローカルでテストが失敗**
   - すべてのテスト依存関係をインストール：`pip install pytest boto3 moto`
   - Pythonバージョン互換性を確認（Python 3.8+が必要）

4. **デプロイメントパッケージが大きすぎる**
   - 現在のセットアップは小さなデプロイメント（<50MB）を処理
   - より大きなパッケージの場合、S3デプロイメントを使用するようワークフローを修正
   - ワークフローファイルのコメントアウトされたS3設定を参照

### ログとモニタリング

Lambda関数のログを表示：

```bash
# 最新のログを表示
aws logs tail /aws/lambda/your-function-name --follow

# 特定のロググループを表示
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/your-function-name
```

GitHub Actionsのモニタリング：
- リポジトリ > Actionsタブに移動
- 特定のワークフロー実行をクリックして詳細なログを表示
- 各ジョブ（test、deploy、dry-run）でエラーを確認

## セキュリティのベストプラクティス

このサンプルはAWSセキュリティのベストプラクティスに従っています：

- ✅ 長期間有効なアクセスキーの代わりにOIDCを使用
- ✅ 最小権限のIAMポリシーを実装
- ✅ 特定のGitHubリポジトリへのアクセス制限
- ✅ デプロイメントロールと実行ロールの分離
- ✅ 機密データに暗号化されたGitHub Secretsを使用

## 次のステップ

このサンプルを拡張するには：

1. **API Gatewayの追加**: REST API統合の作成
2. **データベースの追加**: DynamoDBまたはRDSとの統合
3. **モニタリングの追加**: CloudWatchダッシュボードとアラームの設定
4. **複数環境の追加**: dev/staging/prod用の個別ワークフロー作成
5. **Infrastructure as Codeの追加**: 完全なインフラストラクチャデプロイメントにAWS CDKまたはTerraformを使用

## リソース

- [AWS Lambda ドキュメント](https://docs.aws.amazon.com/lambda/)
- [GitHub Actions AWS Lambda Deploy](https://github.com/aws-actions/aws-lambda-deploy)
- [AWS Lambda GitHub Actions ガイド](https://docs.aws.amazon.com/lambda/latest/dg/deploying-github-actions.html)
- [GitHub ActionsでのAWS OIDC](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

## ライセンス

このサンプルはMITライセンスの下で提供されています。詳細はLICENSEファイルを参照してください。