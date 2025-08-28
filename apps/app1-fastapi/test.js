// save as list_sgs_profiles.js
import { EC2Client, DescribeSecurityGroupsCommand } from "@aws-sdk/client-ec2";
import { fromIni } from "@aws-sdk/credential-providers";
import { loadSharedConfigFiles } from "@aws-sdk/shared-ini-file-loader";

// Helper function to get region from profile
async function getRegionFromProfile(profile) {
  const { configFile } = await loadSharedConfigFiles();
  const region = configFile[profile]?.region;
  if (!region) {
    console.warn(`[${profile}] No region configured, defaulting to us-east-1`);
    return "us-east-1";
  }
  return region;
}

// Function to list security groups for a single profile
async function listSGs(profile) {
  const region = await getRegionFromProfile(profile);
  const client = new EC2Client({
    credentials: fromIni({ profile }),
    region: region,
  });

  try {
    const data = await client.send(new DescribeSecurityGroupsCommand({}));
    console.log(`[${profile} - ${region}] Security Groups (${data.SecurityGroups.length}):`);
    data.SecurityGroups.forEach((sg) => {
      console.log(` - ${sg.GroupName} (${sg.GroupId})`);
    });
  } catch (err) {
    console.error(`[${profile} - ${region}] Error:`, err.message);
  }
}

// Main function
async function main() {
  const profiles = process.argv.slice(2); // get profiles from CLI
  if (profiles.length === 0) {
    console.log("Usage: node list_sgs_profiles.js <profile1> <profile2> ...");
    return;
  }

  // Run all profiles concurrently
  await Promise.all(profiles.map(listSGs));

  console.log("Done listing all security groups.");
}

main();
