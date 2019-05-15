import os
import boto3
import json
import logging
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s %(module)-20s %(lineno)5d %(levelname)-8s %(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
LOG_FILENAME = 'hashtag.log'

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATEFMT, filename=LOG_FILENAME)

if LOG_LEVEL == logging.DEBUG:
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)

ACCESS_KEY_ID="key_user"
ACCESS_KEY_SECRET="secret_user"
ec2 = boto3.resource('ec2',aws_access_key_id="key_user", aws_secret_access_key="secret_user", region_name="us-east-2")
ec2_client = boto3.client('ec2',aws_access_key_id="key_user", aws_secret_access_key="secret_user", region_name="us-east-2")

ec2Regions = {
    'us-east-2' : 'vpc-49c4fd32'    
}
ec2SecurityGroups = {
    'us-east-2' : ['sg-0dd4916477e22148f','sg-06f1214649fb7d4e6']
}
ec2_resources = {}
ec2_clients = {}
ec2_vpcs={}
for region in ec2Regions.keys():
    ec2_resources[region] = boto3.resource('ec2',aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key=ACCESS_KEY_SECRET, region_name=region)
    ec2_clients[region] = boto3.client('ec2',aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key=ACCESS_KEY_SECRET, region_name=region)
    ec2_vpcs[region] = ec2_resources[region].Vpc(ec2Regions[region])

# Default Values
defaultInstanceType='c5.xlarge'

@app.route('/api/ec2InstanceClients', methods=['POST'])
def ec2InstanceCreateClients():
    params = request.get_json()
    print('Received params %s', params)
    imageId=params.get('imageId', 'ami-990e0fff')
    #UserData parameters
    userData = params.get('userData','')
    regionId = params.get('region','eu-west-1')
    subnetId = params.get('subnetId','subnet-2701417f')
    tagName = params.get('tagName','GS_Test')
    instanceType = params.get('instanceType',defaultInstanceType) #'c5.2xlarge')
    instanceCount = params.get('instanceCount',1)
    instanceCount=int(instanceCount)
    print ("Modified instace count as ", instanceCount)
    print ("Received user data as ", userData)
    print ("Received AMI id is ", imageId)
    print ("Received region id is ", regionId)
    print ("Received subnet id is ", subnetId)
    
    resp = {}

    ec2r = ec2_resources[regionId]
    print (ec2r)
    for subnet in ec2r.subnets.all():
        print ("SubnetId : ", subnet.subnet_id)
        print ("zone : ", subnet.availability_zone)

    createdInstances = ec2r.create_instances(
            ImageId=imageId,
            SecurityGroupIds=ec2SecurityGroups[regionId],
            UserData=userData,
            InstanceType=instanceType,
            SubnetId=subnetId,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': tagName
                        }
                    ]
                }
            ],
            MinCount=1,
            MaxCount=instanceCount
        )
    print ("Created instances ")
    
    instance_ids=[]
    for instance in createdInstances:
        instance_ids.append(instance.id)

    # wait for instances to get into running state
    print("Instances are getting initialized. May take few minutes.")
    ec2c = ec2_clients[regionId]
    run_state_waiter = ec2c.get_waiter('instance_running')
    run_state_waiter.wait(InstanceIds=instance_ids)

    resp = []
    resp = getInstanceInfoResp(createdInstances)
    
    ## get details of the instances
    #print("Instances are in running state now. Now waiting for status checks to complete. May take few minutes.")
    #run_state_waiter = ec2_client.get_waiter('instance_status_ok')
    #run_state_waiter.wait(InstanceIds=instance_ids)
    #print("Instances initialization completed.")
    return jsonify (resp)


@app.route('/api/ec2InstanceClients', methods=['DELETE'])
def ec2InstanceTerminateClients():
    params = request.get_json()
    print('Received params %s', params)
    tagName = params.get('tagName','GS_Test')
    instanceIdList = params.get('instanceIdList','')
    
    print('Received params tagName {0} '.format(tagName))
    for id in instanceIdList:
        print (id)
    
    resp = []
    response = ec2_client.terminate_instances(
            InstanceIds=instanceIdList
        )

    print ("Initiated terminate instances ")
    instances = response.get("TerminatingInstances", None)
    resp = getInstanceStateResp(instances)
    #for inst in instances:
    #    data={}
    #    data['id'] =  inst['InstanceId']
    #    data['state'] =  inst['CurrentState']['Name']
    #    data['oldState'] =  inst['PreviousState']['Name']
    #    resp.append(data)
    #   print ("Terminated id {0}, State {1}, prevState {2}".format(inst['InstanceId'],inst['CurrentState']['Name'], inst['PreviousState']['Name']))
    
    return jsonify (resp)

 
@app.route('/api/ec2StartStopClients', methods=['POST'])
def ec2InstanceStartClients():
    params = request.get_json()
    print('Received params %s', params)
    tagName = params.get('tagName','GS_Test')
    instanceIdList = params.get('instanceIdList','')
    
    print('Received params tagName {0} '.format(tagName))
    for id in instanceIdList:
        print (id)
    
    resp = []
    response = ec2_client.start_instances(
            InstanceIds=instanceIdList
        )

    print ("Initiated Start instances ")
    instances = response.get("StartingInstances", None)
    resp = getInstanceStateResp(instances)
    #for inst in instances:
    #    data={}
    #    data['id'] =  inst['InstanceId']
    #    data['state'] =  inst['CurrentState']['Name']
    #    data['oldState'] =  inst['PreviousState']['Name']
    #    resp.append(data)
    #   print ("started id {0}, State {1}, prevState {2}".format(inst['InstanceId'],inst['CurrentState']['Name'], inst['PreviousState']['Name']))
    
    return jsonify (resp)

@app.route('/api/ec2StartStopClients', methods=['DELETE'])
def ec2InstanceStopClients():
    params = request.get_json()
    print('Received params %s', params)
    tagName = params.get('tagName','GS_Test')
    instanceIdList = params.get('instanceIdList','')
    
    print('Received params tagName {0} '.format(tagName))
    for id in instanceIdList:
        print (id)
    
    resp = []
    response = ec2_client.stop_instances(
            InstanceIds=instanceIdList
        )

    print ("Initiated Stop instances ")
    instances = response.get("StoppingInstances", None)
    resp = getInstanceStateResp(instances)
    #for inst in instances:
    #    data={}
    #    data['id'] =  inst['InstanceId']
    #    data['state'] =  inst['CurrentState']['Name']
    #    data['oldState'] =  inst['PreviousState']['Name']
    #    resp.append(data)
    #    print ("Stopped id {0}, State {1}, prevState {2}".format(inst['InstanceId'],inst['CurrentState']['Name'], inst['PreviousState']['Name']))
    
    return jsonify (resp)

    
#based on InstanceIdList
@app.route('/api/ec2ClientStatus/ec2id', methods=['GET'])
def ec2ClientIdStatus():
    instanceIdStr = request.args.get("instanceIdList")
    instanceIdList=[]
    if instanceIdStr is None:
        print ("No instanceId provided")
        return jsonify (instanceIdList)
    else:
        instanceIdList = instanceIdStr.split(',')
        
    print ("Printing received IDs")
    for id in instanceIdList:
        print (id)
    
    resp = []
    instances = ec2.instances.filter(InstanceIds=instanceIdList)
    resp = getInstanceInfoResp(instances)
    
    return jsonify (resp)
    
# based on InstanceIpList
@app.route('/api/ec2ClientStatus/ec2ip', methods=['GET'])
def ec2ClientIPStatus():
    instanceIpStr = request.args.get("instanceIpList")
    instanceIpList=[]
    resp = []
    if instanceIpStr is None:
        print ("No IP provided")
        return jsonify (resp)
    else:
        instanceIpList = instanceIpStr.split(',')
    print ("Printing received IPs")
    for id in instanceIpList:
        print (id)
    
    instances = ec2.instances.filter(Filters=[{'Name': 'public-ip-address', 'Values': instanceIpList}])
    resp = getInstanceInfoResp(instances)
    
    return jsonify (resp)

# based on tag:<Name>&Value
@app.route('/api/ec2ClientStatus/tag', methods=['GET'])
def ec2ClientTagNameStatus():
    tagName = request.args.get("tagName")
    tagValue = request.args.get("tagValue")
    resp = []
    if tagName is None or tagValue is None:
        return jsonify (resp)
    instances = ec2.instances.filter(Filters=[{'Name': 'tag:'+tagName, 'Values': [tagValue]}])
    resp = getInstanceInfoResp(instances)
    
    return jsonify (resp)

# based on tag:Name&Value, state(default running), type (default c5.2xlarge)
#@app.route('/api/v02/ec2ClientStatus', methods=['GET'])
@app.route('/api/ec2ClientStatus', methods=['GET'])
def ec2ClientStatusV02():
    stateStr = request.args.get("state")
    resp = []
    state = []
    if stateStr is None:
        print ("No state provided using running state")
        state = ['running']
    else:
        print ("Printing state")
        state = stateStr.split(',')
        for st in state:
            print (st)
    
    typeStr = request.args.get("type")
    type = []
    if typeStr is None:
        print ("No instance type provided using {0}".format(defaultInstanceType)) #c5.2xlarge")
        type = [defaultInstanceType] #['c5.2xlarge']
    else:
        print ("Printing type")
        type = typeStr.split(',')
        for ty in type:
            print (ty)
    
    for region in ec2_resources.keys():
        regionData={}
        regionData["region"] = region
        ec2r = ec2_resources[region]        
        instances = ec2r.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': state},{'Name': 'instance-type', 'Values': type}])    
        print ("Printing aws instances for region {0}".format(region))
        regionData['instances'] = getInstanceInfoResp(instances)
        resp.append(regionData)
        print ("Received getInstanceInfoResp as ")
        print (resp)
    
    return jsonify (resp)

# based on tag:Name&Value, state(default running), type (default c5.2xlarge)
#@app.route('/api/ec2ClientStatus', methods=['GET'])
@app.route('/api/v01/ec2ClientStatus', methods=['GET'])
def ec2ClientStatus():
    #nameTag = request.args.get("tagNAME")
    stateStr = request.args.get("state")
    state = []
    if stateStr is None:
        print ("No state provided using running state")
        state = ['running']
    else:
        print ("Printing state")
        state = stateStr.split(',')
        for st in state:
            print (st)
    
    typeStr = request.args.get("type")
    type = []
    if typeStr is None:
        print ("No instance type provided using {0}".format(defaultInstanceType)) #c5.2xlarge")
        type = [defaultInstanceType] #['c5.2xlarge']
    else:
        print ("Printing state")
        type = typeStr.split(',')
        for ty in type:
            print (ty)
    
    #for region in ec2_resources.keys():
    #        regionData={}
    ##        regionData["region"] = region
    #        vpc = ec2_vpcs[region]
    #        regionData['vpcId']=vpc.vpc_id    
    #if nameTag is None:
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': state},{'Name': 'instance-type', 'Values': type}])
    #else:
    #    instances = ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': [nameTag]},{'Name': 'instance-state-name', 'Values': state},{'Name': 'instance-type', 'Values': type}])
    print ("Printing aws instances")
    resp = getInstanceInfoResp(instances)
    
    return jsonify (resp)


def getInstanceStateResp(instances):
    resp = []
    for inst in instances:
        data={}
        data['id'] =  inst['InstanceId']
        data['state'] =  inst['CurrentState']['Name']
        data['oldState'] =  inst['PreviousState']['Name']
        resp.append(data)
        print ("Id {0}, State {1}, prevState {2}".format(inst['InstanceId'],inst['CurrentState']['Name'], inst['PreviousState']['Name']))
    return resp

def getInstanceInfoResp(instances):
    resp = []
    for instance in instances:
        data={}
        print(" Instance Id: {0}, Type: {1}, State: {2}".format(instance.id, instance.instance_type, instance.state['Name']))
        if instance.tags:
            print ("     TAG {0} = {1}".format(instance.tags[0]['Key'], instance.tags[0]['Value']))
            data[instance.tags[0]['Key']]=instance.tags[0]['Value']
        if instance.public_ip_address:
            print ("     Private IP: ", instance.public_ip_address)
        data['ip']=instance.public_ip_address
        data['state']=instance.state['Name']
        data['id']=instance.id
        data['type']=instance.instance_type
        data['zone']=instance.placement['AvailabilityZone']
        # check if tag:Name is defined or else save all tags
        #data['launchTime']=instance.launch_time
        resp.append(data)
        print (resp)
    return resp

def getRegionAMIList(region):
    resp = []
    amiList = []
    owner="self"
    print ("Retriving for region {0} for owner {1}".format(region, owner))
    #amiList = ec2.images.filter(Owners=[owner])
    amiList = ec2_resources[region].images.filter(Owners=[owner])
    
    print ("Received AMI List")
    for image in amiList:
        data={}
        data["amiId"] = image.image_id
        data["amiName"] = image.name
        data["creationdate"] = image.creation_date
        resp.append(data)
    print ("AMI Details are ")
    print (resp)
    #resp.append(data)
    return resp

# based on tag:Name&Value, state(default running), type (default c5.2xlarge)
@app.route('/api/amilist', methods=['GET'])
def ec2AmiList():
    regionStr = request.args.get("region")
    owner="self"
    resp = []
    amiList = []
    if regionStr is None:
        # Get AMI's from all regions
        for region in ec2_vpcs.keys():
            regionData={}
            regionImages = getRegionAMIList(region)
            regionData["region"] = region
            regionData["images"] = regionImages
            resp.append(regionData)
    else:
        print ("Retriving for region {0} for owner {1}".format(regionStr, owner))
        regionData={}
        regionImages = getRegionAMIList(regionStr)
        regionData["region"] = regionStr
        regionData["images"] = regionImages
        resp.append(regionData)
    
    print ("AMI Details are ")
    print (resp)
    
    return jsonify (resp)

# Return subnets based on regions and VPC's configured
@app.route('/api/subnetlist', methods=['GET'])
def ec2SubnetList():
    resp=[]
    for region in ec2_vpcs.keys():
        vpc = ec2_vpcs[region]
        vpcdata = {}
        vpcdata['vpcId']=vpc.vpc_id
        vpcdata['region']=region
        subnetList = getSubnetList(region)
        vpcdata['subnetList']=subnetList
        resp.append(vpcdata)
        
    return jsonify (resp)

# based on tag:Name&Value, state(default running), type (default c5.2xlarge)
@app.route('/api/regions', methods=['GET'])
def ec2RegionList():
    region = request.args.get("region")
    owner="self"
    resp = []
    amiList = []
    if region is None:
        # Get AMI's from all regions
        for region in ec2_vpcs.keys():
            regionData={}
            regionData["region"] = region
            vpc = ec2_vpcs[region]
            regionData['vpcId']=vpc.vpc_id
            regionImages = getRegionAMIList(region)
            regionData["images"] = regionImages
            subnetList = getSubnetList(region)
            regionData['subnetList']=subnetList
            resp.append(regionData)
    else:
        print ("Retriving for region {0} for owner {1}".format(region, owner))
        regionData={}
        regionData["region"] = region
        vpc = ec2_vpcs[region]
        regionData['vpcId']=vpc.vpc_id
        regionImages = getRegionAMIList(region)
        regionData["images"] = regionImages
        subnetList = getSubnetList(region)
        regionData['subnetList']=subnetList
        resp.append(regionData)
    
    print ("AMI Details are ")
    print (resp)
    
    return jsonify (resp)

def getSubnetList(region):
    vpc = ec2_vpcs[region]
    subnetList = []
    for subnet in vpc.subnets.all():
        subnetInfo = {}
        print (vpc, "all:", subnet)
        subnetInfo['id']=subnet.subnet_id
        subnetInfo['zone']=subnet.availability_zone
        if subnet.tags is None:
            # If subnet name is not assigned then we use subnet id as its name
            subnetInfo['name'] = subnet.subnet_id
        elif len(subnet.tags) > 0:
            subnetInfo['name']=subnet.tags[0]['Value']
        else:
            # If subnet name is not assigned then we use subnet id as its name
            subnetInfo['name']=subnet.subnet_id
        subnetList.append(subnetInfo)
    return subnetList

##### To run it as flask service execute the following    
#set FLASK_APP=D:\collegues\Sameer\Hashtag_AGST\HashtagAwsAPI.py
#flask run --host=0.0.0.0 
    
#if __name__ == '__main__':
#   client = ec2InstStartClients()
#app.run(debug=True, host='0.0.0.0')
#if __name__ == '__main__':
#    app.run(host='0.0.0.0', debug=True)