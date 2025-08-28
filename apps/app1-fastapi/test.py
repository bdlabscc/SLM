import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.config import Config

def fetch_security_group_count(profile_name):
    try:
        # Create a session with the given profile
        session = boto3.Session(profile_name=profile_name)
        ec2_client = session.client(
            'ec2',
            config=Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
        )
        
        # Fetch security groups and return count
        response = ec2_client.describe_security_groups()
        sg_count = len(response['SecurityGroups'])
        return {profile_name: sg_count}
    except Exception as e:
        return {profile_name: f'Error: {str(e)}'}

def get_security_group_counts(profile_names):
    results = {}
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=50) as executor:  # Adjust max_workers as needed
        futures = [executor.submit(fetch_security_group_count, profile) for profile in profile_names.split()]
        for future in as_completed(futures):
            results.update(future.result())
    return results

if __name__ == "__main__":
    # Example: Pass profile names as space-separated string
    profiles_input = input("Enter AWS profile names separated by spaces: ")
    result = get_security_group_counts(profiles_input)
    for profile, count in result.items():
        print(f"Profile {profile}: {count}")