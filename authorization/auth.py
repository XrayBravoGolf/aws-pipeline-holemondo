import re
import os
import boto3

def lambda_handler(event, context):

    token = event['authorizationToken']

    principalId = 'principalId 0'

    splitArn = event['methodArn'].split(':')
    apiGatewayArnTmp = splitArn[5].split('/')
    awsAccountId = splitArn[4]

    policy = AuthPolicy(principalId, awsAccountId)
    policy.restApiId = apiGatewayArnTmp[0]
    policy.region = splitArn[3]
    policy.stage = apiGatewayArnTmp[1]

    allowTable = {"principalId 0":{"/event":"GET"}}

    for k,v in allowTable[principalId]:
        policy.allowMethod(v, k) # "GET", "/event"

    authResponse = policy.build()
    print(authResponse)  
    return authResponse

class HttpVerb:
    GET     = "GET"
    POST    = "POST"
    PUT     = "PUT"
    PATCH   = "PATCH"
    HEAD    = "HEAD"
    DELETE  = "DELETE"
    OPTIONS = "OPTIONS"
    ALL     = "*"

class AuthPolicy(object):
    awsAccountId = ""
    principalId = ""
    version = "2012-10-17"
    pathRegex = "^[/.a-zA-Z0-9-\*]+$"
    allowMethods = []
    denyMethods = []

    restApiId = "*"
    region = "*"
    stage = "*"

    def __init__(self, principal, awsAccountId):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods = []
        self.denyMethods = []

    def _addMethod(self, effect, verb, resource, conditions):
        if verb != "*" and not hasattr(HttpVerb, verb):
            raise NameError("Invalid HTTP verb " + verb + ". Allowed verbs in HttpVerb class")
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError("Invalid resource path: " + resource + ". Path should match " + self.pathRegex)

        if resource[:1] == "/":
            resource = resource[1:]

        resourceArn = ("arn:aws:execute-api:" +
            self.region + ":" +
            self.awsAccountId + ":" +
            self.restApiId + "/" +
            self.stage + "/" +
            verb + "/" +
            resource)

        if effect.lower() == "allow":
            self.allowMethods.append({
                'resourceArn' : resourceArn,
                'conditions' : conditions
            })
        elif effect.lower() == "deny":
            self.denyMethods.append({
                'resourceArn' : resourceArn,
                'conditions' : conditions
            })

    def _getEmptyStatement(self, effect):
        statement = {
            'Action': 'execute-api:Invoke',
            'Effect': effect[:1].upper() + effect[1:].lower(),
            'Resource': []
        }

        return statement

    def _getStatementForEffect(self, effect, methods):
        statements = []

        if len(methods) > 0:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if curMethod['conditions'] is None or len(curMethod['conditions']) == 0:
                    statement['Resource'].append(curMethod['resourceArn'])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement['Resource'].append(curMethod['resourceArn'])
         
                    statements.append(conditionalStatement)

            statements.append(statement)

        return statements

    def allowAllMethods(self):
        self._addMethod("Allow", HttpVerb.ALL, "*", [])

    def denyAllMethods(self):
        self._addMethod("Deny", HttpVerb.ALL, "*", [])

    def allowMethod(self, verb, resource):
        self._addMethod("Allow", verb, resource, [])

    def denyMethod(self, verb, resource):
        self._addMethod("Deny", verb, resource, [])

    def allowMethodWithConditions(self, verb, resource, conditions):
        self._addMethod("Allow", verb, resource, conditions)

    def denyMethodWithConditions(self, verb, resource, conditions):
        self._addMethod("Deny", verb, resource, conditions)

    def build(self):
        if ((self.allowMethods is None or len(self.allowMethods) == 0) and
            (self.denyMethods is None or len(self.denyMethods) == 0)):
            raise NameError("No statements defined for the policy")

        policy = {
            'principalId' : self.principalId,
            'policyDocument' : {
                'Version' : self.version,
                'Statement' : []
            }
        }

        policy['policyDocument']['Statement'].extend(self._getStatementForEffect("Allow", self.allowMethods))
        policy['policyDocument']['Statement'].extend(self._getStatementForEffect("Deny", self.denyMethods))

        return policy