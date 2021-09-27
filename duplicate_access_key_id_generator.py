import threading
import time
import boto3

ROLE_TO_ASSUME = 'arn:aws:iam::111111111111:role/TestAssumeRoleRaceRole' # Change this to be a role you can assume
ROLE_SESSION_NAME = 'TestRaceSessionName' # Role session name used in assume role calls
NUMBER_OF_RUNS = 60*60*2 # Number of total runs
THREADS_PER_RUN = 180 # Number of AssumeRole calls per run interval
RUN_INTERVAL = 1 # Time interval between each run
OUTPUT_FILE_NAME = 'duplicate_access_keys.log'

SUCCESS = 0

sts = boto3.client('sts')

all_access_keys = set()
all_credential_sets = set()

def assume_role():
    response = sts.assume_role(
    	RoleArn=ROLE_TO_ASSUME,
    	RoleSessionName=ROLE_SESSION_NAME
    )
    return response


class myThread(threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name

	def run(self):
		response = assume_role()
		if "Credentials" in response and "AccessKeyId" in response['Credentials']:
			access_key = response['Credentials']['AccessKeyId']
			secret_access_key = response['Credentials']['SecretAccessKey']
			session_token = response['Credentials']['SessionToken']

			if access_key != '' and access_key is not None:
				print(str(self.threadID) + ': ' + str(response['Credentials']['AccessKeyId']))
				if access_key in all_access_keys:
					output_str = ("########################################################\n")
					output_str += ("#                                                      #\n")
					output_str += ("#            FOUND DUPLICATE ACCESS KEY ID!            #\n")
					output_str += ("#                 " + access_key + "     #\n")
					output_str += ("#                                                      #\n")
					output_str += ("#                                                      #\n")
					output_str += ("#      Both access key details are:        #\n")					
					output_str += "#  " + str([credential_set for credential_set in all_credential_sets if credential_set[0] == access_key]) + "  #\n"
					output_str += "#  " + str((access_key, secret_access_key, session_token)) + "  #\n"
					output_str += ("#                                                      #\n")
					output_str += ("########################################################\n")
					print(output_str)
					open(OUTPUT_FILE_NAME, 'a+').write(output_str)
				all_access_keys.add(access_key)
				all_credential_sets.add((access_key, secret_access_key, session_token))


def main():
	k = 0
	for i in range(NUMBER_OF_RUNS):
		for j in range(THREADS_PER_RUN):
			k += 1
			thread_obj = myThread(k, "Thread-" + str(k))
			thread_obj.start()
		time.sleep(RUN_INTERVAL)

	return SUCCESS


if __name__ == "__main__":
	main()
