import boto3
import json
import time, random 
import uuid, string
import matplotlib.pyplot as plt
import io

class CodeExecutorAgent:
    def __init__(self, agent_name):
        self.region_name = 'us-east-1'
        self.bedrock_agent = boto3.client(service_name = 'bedrock-agent', region_name = self.region_name)
        self.iam = boto3.client('iam')
        self.agentName = agent_name#'code-interpreter-test-agent'
        self.instruction = """
        You are an advanced AI agent with the capability to execute Python code. Here are your tasks:

            1. Execute the provided Python code exactly as given.
            2. If the code does not work or is incorrect, modify the code to correct errors and run again.
            3. After correcting the code, test it to ensure it works as expected.
            4. Return the final executed code, or if not possible to correct after 5 attempts, return the best attempt with a note on remaining issues.
                        """
        self.foundationModel = 'anthropic.claude-3-sonnet-20240229-v1:0'
        self.randomSuffix = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        self.roles_and_policies()
        self.create_agent()
        self.configure_code_interpreter()
        self.prepare_agent()
    
    def roles_and_policies(self):
        
        print("Creating the IAM policy and role...")

        # Define IAM trust policy
        trustPolicy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        # Define IAM policy for invoking the foundation model
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{self.region_name}::foundation-model/{self.foundationModel}"
                    ]
                }
            ]
        }

        role_name = f"test-agent-{self.randomSuffix}"
        role = self.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument = json.dumps(trustPolicy)
        )
        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName = f"policy-test-agent-{self.randomSuffix}",
            PolicyDocument = json.dumps(policy)
        )

        self.roleArn = role['Role']['Arn']

        print(f"IAM Role: {self.roleArn[:13]}{'*' * 12}{self.roleArn[25:]}")

    def create_agent(self):

        print("Creating the agent...")

        # Create the Bedrock Agent
        response = self.bedrock_agent.create_agent(
            agentName=f"{self.agentName}-{self.randomSuffix}",
            foundationModel=self.foundationModel,
            instruction=self.instruction,
            agentResourceRoleArn=self.roleArn,
        )

        self.agentId = response['agent']['agentId']

        print("Waiting for agent status of 'NOT_PREPARED'...")

        # Wait for agent to reach 'NOT_PREPARED' status
        agentStatus = ''
        while agentStatus != 'NOT_PREPARED':
            response = self.bedrock_agent.get_agent(
                agentId = self.agentId
            )
            agentStatus = response['agent']['agentStatus']
            print(f"Agent status: {agentStatus}")
            time.sleep(2)

    def configure_code_interpreter(self):

        ######################################### Configure code interpreter for the agent
        response = self.bedrock_agent.create_agent_action_group(
            
            actionGroupName='CodeInterpreterAction',
            actionGroupState='ENABLED',
            agentId=self.agentId,
            agentVersion='DRAFT',

            parentActionGroupSignature='AMAZON.CodeInterpreter' # <-  To allow your agent to generate, 
                                                                #     run, and troubleshoot code when trying 
                                                                #     to complete a task, set this field to 
                                                                #     AMAZON.CodeInterpreter. 
                                                                #     You must leave the `description`, `apiSchema`, 
                                                                #     and `actionGroupExecutor` fields blank for 
                                                                #     this action group.
        )

        actionGroupId = response['agentActionGroup']['actionGroupId']

        print("Waiting for action group status of 'ENABLED'...")

        # Wait for action group to reach 'ENABLED' status
        actionGroupStatus = ''
        while actionGroupStatus != 'ENABLED':
            response = self.bedrock_agent.get_agent_action_group(
                agentId=self.agentId,
                actionGroupId=actionGroupId,
                agentVersion='DRAFT'
            )
            actionGroupStatus = response['agentActionGroup']['actionGroupState']
            print(f"Action Group status: {actionGroupStatus}")
            time.sleep(2)

    def prepare_agent(self):

        print("Preparing the agent...")

        # Prepare the agent for use
        response = self.bedrock_agent.prepare_agent(
            agentId=self.agentId
        )

        print("Waiting for agent status of 'PREPARED'...")

        # Wait for agent to reach 'PREPARED' status
        agentStatus = ''
        while agentStatus != 'PREPARED':
            response = self.bedrock_agent.get_agent(
                agentId=self.agentId
            )
            agentStatus = response['agent']['agentStatus']
            print(f"Agent status: {agentStatus}")
            time.sleep(2)

        print("Creating an agent alias...")

        # Create an alias for the agent
        response = self.bedrock_agent.create_agent_alias(
            agentAliasName='test',
            agentId=self.agentId
        )

        self.agentAliasId = response['agentAlias']['agentAliasId']

        # Wait for agent alias to be prepared
        agentAliasStatus = ''
        while agentAliasStatus != 'PREPARED':
            response = self.bedrock_agent.get_agent_alias(
                agentId=self.agentId,
                agentAliasId=self.agentAliasId
            )
            agentAliasStatus = response['agentAlias']['agentAliasStatus']
            print(f"Agent alias status: {agentAliasStatus}")
            time.sleep(2)

        print('Done.\n')

        print(f"agentId: {self.agentId}, agentAliasId: {self.agentAliasId}")