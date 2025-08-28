// save this as list_sgs.js
import { EC2Client, DescribeSecurityGroupsCommand } from "@aws-sdk/client-ec2";
import { fromIni } from "@aws-sdk/credential-providers";

async function listSGs(profile) {
  const client = new EC2Client({
    region: "us-east-1", // change region if needed
    credentials: fromIni({ profile }),
  });

  try {
    const data = await client.send(new DescribeSecurityGroupsCommand({}));
    console.log(`[${profile}] Security Groups (${data.SecurityGroups.length}):`);
    data.SecurityGroups.forEach((sg) => {
      console.log(` - ${sg.GroupName} (${sg.GroupId})`);
    });
  } catch (err) {
    console.error(`[${profile}] Error:`, err.message);
  }
}

async function main() {
  const profiles = process.argv.slice(2); // get profile names from CLI
  if (profiles.length === 0) {
    console.log("Usage: node list_sgs.js <profile1> <profile2> ...");
    return;
  }

  // Run all profiles concurrently
  await Promise.all(profiles.map(listSGs));

  console.log("Done listing all security groups.");
}

main();
