from aws_cdk import (
    BundlingOptions,
    Duration,
    Stack,
    aws_apigateway as apigw_,
    aws_lambda as lambda_,
    aws_cognito as cognito_,
    aws_dynamodb as dynamodb_,
    aws_s3 as s3_,
    aws_s3_deployment as s3_deployment_,
    aws_route53 as route53_,
    aws_route53_targets as route53_targets_,
    aws_certificatemanager as acm_,
    aws_cloudfront as cloudfront_,
    aws_cloudfront_origins as origins_,
    aws_secretsmanager as secretsmanager
)
from constructs import Construct

class ApiScope():
    def __init__(self, api_scope: cognito_.ResourceServerScope, resource_server: cognito_.UserPoolResourceServer, resource_server_identifier: str):
        self.api_scope = api_scope
        self.resource_server = resource_server
        self.resource_server_identifier = resource_server_identifier
        self.auth_scope = f'{resource_server_identifier}/{api_scope.scope_name}'

# still need to apply proper removal policies and delete protection.

class HealthConnectorCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # secret = secretsmanager.Secret.from_secret_name_v2(self, 'dev_credentials', 'dev_credentials')
        secret = secretsmanager.Secret.from_secret_name_v2(self, 'prod_credentials', 'prod_credentials')

        table_name = 'MOD_Medicaid'
        table = dynamodb_.TableV2(
            self,
            'HealthConnectorMODMedicaidTable',
            table_name=table_name,
            contributor_insights=True,
            billing=dynamodb_.Billing.on_demand(),
            point_in_time_recovery=True,
            partition_key=dynamodb_.Attribute(
                name='atms_ride_id',
                type=dynamodb_.AttributeType.STRING
            )
        )

        table_name2 = 'MOD_Medicaid_History'
        table2 = dynamodb_.TableV2(
            self,
            'HealthConnectorMODMedicaidHistoryTable',
            table_name=table_name2,
            contributor_insights=True,
            billing=dynamodb_.Billing.on_demand(),
            point_in_time_recovery=True,
            partition_key=dynamodb_.Attribute(
                name='atms_ride_id',
                type=dynamodb_.AttributeType.STRING
            ),
            global_secondary_indexes=[dynamodb_.GlobalSecondaryIndexPropsV2(
                            index_name='g111',
                            partition_key=dynamodb_.Attribute(
                                name='update_time',
                                type=dynamodb_.AttributeType.STRING
                            ),
                        )],
        )


        # api handler lambda function.
        api_handler = lambda_.Function(
            self,
            'HealthConnectorApiHandler',
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset('lambda',
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=["bash", "-c", "pip install -r requirements.txt -t /asset-output && rsync -r . /asset-output"
                ])
            ),
            handler='health_connector.api_handler',
            timeout=Duration.minutes(1),
            environment={
                'TABLE_NAME': table_name,
                'Execution': "On_AWS"
            }
        )

        secret.grant_read(api_handler.role)

        dashboard_handler = lambda_.Function(
            self,
            'HealthConnectorDashboardHandler',
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset('lambda'),
            handler='health_connector.dashboard_handler',
            environment={
                'TABLE_NAME': table_name
            }
        )
        kiosk_workerbee = lambda_.Function(
            self,
            'HealthConnectorKioskWorker',
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset('lambda',
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=["bash", "-c", "pip install -r requirements.txt -t /asset-output && rsync -r . /asset-output"
                ])
            ),
            handler='health_connector.lambda_kiosk',
            timeout=Duration.minutes(10),
            environment={
                'TABLE_NAME': table_name
            }
        )

        secret.grant_read(kiosk_workerbee.role)
        
        kiosk_statusbee = lambda_.Function(
            self,
            'HealthConnectorKioskStatus',
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset('lambda',
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=["bash", "-c", "pip install -r requirements.txt -t /asset-output && rsync -r . /asset-output"
                ])
            ),
            handler='health_connector.lambda_kiosk_status',
            timeout=Duration.minutes(10),
            environment={
                'TABLE_NAME': table_name
            }
        )

        secret.grant_read(kiosk_statusbee.role)

        lyft_tapi_trips = lambda_.Function(
            self,
            'HealthConnectorTAPITrips',
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset('lambda',
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=["bash", "-c", "pip install -r requirements.txt -t /asset-output && rsync -r . /asset-output"
                ])
            ),
            handler='health_connector.lambda_lyft_tapi_trips_v1',
            timeout=Duration.minutes(10),
            environment={
                'TABLE_NAME': table_name
            }
        )

        table.grant_read_write_data(lyft_tapi_trips)
        table.grant_read_write_data(api_handler)
        table2.grant_read_write_data(api_handler)
        table.grant_read_data(dashboard_handler)


        domain_name = 'hirtahealthconnector.org'
        # domain_name = 'hirtahealthconnector.org'
        hosted_zone = route53_.HostedZone.from_lookup(
            self,
            'HealthConnectorHostedZone',
            domain_name=domain_name
        )
        # had to create manually in us-east-1 for cloudfront.
        us_east_1_certificate = acm_.Certificate.from_certificate_arn(
            self,
            'HealthConnectorCertificateUsEast1',
            # certificate_arn='arn:aws:acm:us-east-1:135808953563:certificate/d76fa1be-fdea-44e4-af22-6e449a1557c2'
            certificate_arn='arn:aws:acm:us-east-1:891377257073:certificate/2ff2ee84-3e12-4701-9628-877fabd5f76c'
        )
        certificate = acm_.Certificate(
            self,
            'HealthConnectorCertificate',
            domain_name=domain_name,
            subject_alternative_names=[
                f'*.{domain_name}'
            ],
            validation=acm_.CertificateValidation.from_dns(hosted_zone)
        )

        # setup the cognito user pool and the oauth scope for the API.
        user_pool, user_pool_domain = self.setup_cognito_user_pool()
        api_scope = self.setup_api_scope(user_pool)

        # call for each machine-to-machine API client.
        self.setup_api_user_pool_client(user_pool, api_scope, 'Lyft')
        self.setup_api_user_pool_client(user_pool, api_scope, 'Pompano')
        self.setup_api_user_pool_client(user_pool, api_scope, 'Via')

        bucket = s3_.Bucket(
            self,
            'HealthConnectorBucket',
            bucket_name='health-connector-website-bucket',
            website_index_document='index.html',
            public_read_access=True,
            block_public_access=s3_.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

        # this one is for Kiosk!!
        cloudfront_distribution = cloudfront_.Distribution(
            self,
            'HealthConnectorCloudFrontDistribution',
            default_behavior=cloudfront_.BehaviorOptions(
                origin=origins_.S3Origin(
                    bucket=bucket
                ),
                viewer_protocol_policy=cloudfront_.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            domain_names=[
                f'dashboard.{domain_name}'
                # f'kiosk.hirta.us'
            ],
            certificate=us_east_1_certificate
        )
        s3_deployment_.BucketDeployment(
            self,
            'HealthConnectorBucketDeployment',
            sources=[s3_deployment_.Source.asset('website/dist')],
            destination_bucket=bucket,
            distribution=cloudfront_distribution,
        )
        route53_.ARecord(
            self,
            'HealthConnectorCloudFrontARecord',
            zone=hosted_zone,
            record_name='dashboard',
            target=route53_.RecordTarget.from_alias(
                route53_targets_.CloudFrontTarget(cloudfront_distribution)
            )
        )

        api_stage_name = 'prod'
        api = apigw_.RestApi(
            self,
            'HealthConnectorApi',
            default_cors_preflight_options=apigw_.CorsOptions(
                allow_origins=apigw_.Cors.ALL_ORIGINS,
                allow_methods=apigw_.Cors.ALL_METHODS
            ), 
            rest_api_name='health_connector',
            deploy=True,
            deploy_options=apigw_.StageOptions(
                stage_name=api_stage_name,
                metrics_enabled=True,
            ),
            domain_name=apigw_.DomainNameOptions(
                domain_name=f'api.{domain_name}',
                certificate=certificate,
                endpoint_type=apigw_.EndpointType.REGIONAL
            )
        )     
        route53_.ARecord(
            self,
            'HealthConnectorApiARecord',
            zone=hosted_zone,
            record_name='api',
            target=route53_.RecordTarget.from_alias(
                route53_targets_.ApiGateway(api)
            )
        )

        authorizer = apigw_.CognitoUserPoolsAuthorizer(
            self,
            'HealthConnectorAuthorizer',
            cognito_user_pools=[user_pool],
            identity_source=apigw_.IdentitySource.header('Authorization')
        )

        # oauth2 endpoint

        api.root.add_resource('oauth2').add_resource('token').add_method(
            'POST',
            # proxy to user pool oauth2/token/ endpoint.
            apigw_.HttpIntegration(
                url=f'https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/oauth2/token',
                http_method='POST'
            )
        )

        ## MOD-MEDICAID ENDPOINTS

        lyft_v1 = api.root.add_resource('v1')
        tapi = lyft_v1.add_resource('tapi')
        tapi_trips = tapi.add_resource('trips')

        tapi_providers = tapi.add_resource('providers')
        tapi_providers.add_method(
            'GET',
            apigw_.LambdaIntegration(
                api_handler,
                # lyft_tapi_trips,
                proxy=True
            ),
            authorizer=authorizer,
            authorization_scopes=[
                api_scope.auth_scope
            ]
        )
        

        tapi_trips.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                # lyft_tapi_trips,
                proxy=True
            ),
            authorizer=authorizer,
            authorization_scopes=[
                api_scope.auth_scope
            ]
        )

        tapi_update = tapi_trips.add_resource('{trip_id}')
        tapi_update.add_method(
            'PUT',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            ),
            authorizer=authorizer,
            authorization_scopes=[
                api_scope.auth_scope
            ]
        )

        tapi_cancel = tapi_update.add_resource('cancel')
        tapi_cancel.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            ),
            authorizer=authorizer,
            authorization_scopes=[
                api_scope.auth_scope
            ]
        )

        ## KIOSK ENDPOINT

        ## DEPRECTATE MEEEE

        connector_resource = api.root.add_resource('connector')
        connector_resource.add_method(
            'POST',
            apigw_.LambdaIntegration(
                kiosk_workerbee,
                proxy=True
            ),
            authorizer=authorizer,
        )

        # Fixing issue around cognito user pool by removing authoirzation scope.
        connector_resource_status = api.root.add_resource('connector_status')
        connector_resource_status.add_method(
            'POST',
            apigw_.LambdaIntegration(
                kiosk_statusbee,
                proxy=True
            ),
            authorizer=authorizer,
        )

        ## THE NEW ONES

        kiosk_resource = api.root.add_resource('kiosk_request')
        kiosk_resource.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            ),
            authorizer=authorizer,
        )
        kiosk_resource = api.root.add_resource('kiosk_request_detail')
        kiosk_resource.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            ),
            authorizer=authorizer,
        )

        kiosk_resource_status = api.root.add_resource('kiosk_status')
        kiosk_resource_status.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            ),
            authorizer=authorizer,
        )

        ## VIA WEBHOOK ENDPOINT
        
        via_webhook = api.root.add_resource('via_webhook')
        via_webhook.add_method(
            'POST',
            apigw_.LambdaIntegration(
                api_handler,
                proxy=True
            )
        )

        ## MOD-EHR ENDPOINTS

        dashboard_resource = api.root.add_resource('dashboard')
        dashboard_resource.add_method(
            'GET',
            apigw_.LambdaIntegration(
                dashboard_handler,
                proxy=True
            ),
            authorizer=authorizer
        )

        self.setup_web_user_pool_client(
            user_pool=user_pool,
            callback_url1='https://kiosk.hirta.us/',
            callback_url2='https://kiosk.hirta.us/static/cognito.html'
        )


    def setup_cognito_user_pool(self) -> tuple[cognito_.UserPool, cognito_.UserPoolDomain]:

        user_pool = cognito_.UserPool(
            self,
            'HealthConnectorUserPool',
            account_recovery=cognito_.AccountRecovery.EMAIL_ONLY,
            auto_verify=cognito_.AutoVerifiedAttrs(
                email=True
            ),
            user_pool_name='health_connector_user_pool',
            self_sign_up_enabled=False,
            sign_in_aliases=cognito_.SignInAliases(
                email=True
            ),
            user_invitation=cognito_.UserInvitationConfig(
                email_subject='Health Connector Invitation',
                email_body='Your username is {username} and temporary password is {####}'
            )
        )

        user_pool_domain = cognito_.UserPoolDomain(
            self,
            'HealthConnectorUserPoolDomain',
            user_pool=user_pool,
            cognito_domain=cognito_.CognitoDomainOptions(
                domain_prefix='health-connector'
            )
        )

        return user_pool, user_pool_domain
    
    def setup_api_scope(self, user_pool: cognito_.UserPool) -> ApiScope:
        api_scope = cognito_.ResourceServerScope(
            scope_name='health_connector',
            scope_description='Health Connector API access'
        )

        resource_server_identifier = 'health_connector_api'
        resrouce_server = cognito_.UserPoolResourceServer(
            self,
            'HealthConnectorResourceServer',
            user_pool=user_pool,
            identifier=resource_server_identifier,
            scopes=[api_scope]
        )

        return ApiScope(
            api_scope=api_scope,
            resource_server=resrouce_server,
            resource_server_identifier=resource_server_identifier
        )

    def setup_api_user_pool_client(self, user_pool: cognito_.UserPool, api_scope: ApiScope, client: str) -> cognito_.UserPoolClient:

        return cognito_.UserPoolClient(
            self,
            f'HealthConnectorUserPoolApiClient-{client}',
            user_pool=user_pool,
            user_pool_client_name=f'api_client_{client}',
            generate_secret=True,
            o_auth=cognito_.OAuthSettings(
                flows=cognito_.OAuthFlows(
                    client_credentials=True
                ),
                scopes=[
                    cognito_.OAuthScope.resource_server(
                        server=api_scope.resource_server,
                        scope=api_scope.api_scope
                    )
                ]
            )
        )

    def setup_web_user_pool_client(self, user_pool: cognito_.UserPool, callback_url1: str, callback_url2: str) -> cognito_.UserPoolClient:

        return cognito_.UserPoolClient(
            self,
            'HealthConnectorUserPoolWebClient',
            user_pool=user_pool,
            user_pool_client_name='health_connector_user_pool_web_client',
            auth_session_validity=Duration.minutes(3),
            refresh_token_validity=Duration.minutes(8 * 24 * 60), # 8 days
            access_token_validity=Duration.minutes(1 * 24 * 60), # 1 day
            id_token_validity=Duration.minutes(1 * 24 * 60), # 1 day
            auth_flows=cognito_.AuthFlow(user_password=True),
            o_auth=cognito_.OAuthSettings(
                flows=cognito_.OAuthFlows(
                    implicit_code_grant=True,
                    authorization_code_grant=True
                ),
                scopes=[
                    cognito_.OAuthScope.OPENID,
                    cognito_.OAuthScope.EMAIL
                ],
                callback_urls=[
                    callback_url1,
                    callback_url2
                ],
                logout_urls=[
                    callback_url1
                ]
            ),
            supported_identity_providers=[
                cognito_.UserPoolClientIdentityProvider.COGNITO
            ]
        )
