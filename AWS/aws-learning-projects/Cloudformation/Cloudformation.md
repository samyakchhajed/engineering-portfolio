# Project 8 – CloudFormation Stack Lifecycle & Ownership

## 1) What this teaches 
- **Infrastructure as Code (IaC) Fundamentals:** Managing AWS through stacks rather than manual console clicks.
- **Resource Ownership:** Understanding that a stack is a unit of ownership that manages a group of resources together through their entire lifecycle (creation, update, and deletion).
- **Lifecycle Control:** Learning that infrastructure changes must be intentional and that safe deletion is a design requirement.
- **Data Protection Guardrails:** Recognizing that AWS enforces safety rules during automation to prevent accidental data loss.
- **Mental Shift:** Transitioning from managing individual AWS resources to managing systems that own those resources.

## 2) Goal 
Understand resource ownership and lifecycle control by deploying a minimal CloudFormation stack, performing safe updates, and navigating intentional deletion failures.

## 3) Architecture / Flow 
1. **Creation:** Deploy a YAML template to create a stack containing an S3 bucket and an IAM role.
2. **Verification:** Confirm the stack owns the resources by navigating to them directly from the CloudFormation console.
3. **Update:** Apply tags to resources to observe in-place updates without resource replacement.
4. **Safety Test:** Upload a file to S3 to trigger a planned deletion failure.
5. **Recovery:** Manually empty the data-bearing resource to allow for a clean, automated deletion of the entire stack.

## 4) AWS Services + Why they were used
- **AWS CloudFormation:** Used as the primary tool to manage the unit of ownership and the resource lifecycle.
- **Amazon S3:** Used to demonstrate how CloudFormation interacts with data-bearing resources and enforces data protection rules.
- **IAM (Identity and Access Management):** Used to observe the lifecycle of infrastructure components that do not have runtime state or data.

## 5) Recreation Guide
### Setup
- Create a YAML template defining a standalone stack named `week9-core-foundation`.
- Include an S3 Bucket (`LearningArtifactsBucket`) with server-side encryption (AES-256) enabled.
- Include an IAM Role (`FutureExecutionRole`) with a trust relationship for Lambda and EC2, and the `AWSLambdaBasicExecutionRole` managed policy attached.

### Execution
- Upload the template to the CloudFormation console in the `ap-south-1` (Mumbai) region.
- Acknowledge that the template may create IAM resources and initiate the stack creation.
- Once `CREATE_COMPLETE` is reached, perform a stack update by adding tags: `project = week9` and `purpose = learning`.
- Verify the stack reaches `UPDATE_COMPLETE` and confirms that no resources were replaced during the update.

### Verification (Proof checks)
- Confirm logical resource names map cleanly to physical AWS resources.
- Ensure the creation order is visible in the CloudFormation events tab.
- Navigate to the S3 and IAM consoles specifically using the links provided within the stack's "Resources" tab to confirm ownership.

### Cleanup
- Upload a small file to the S3 bucket.
- Attempt to delete the stack and observe that it enters the `DELETE_FAILED` state.
- Confirm the IAM Role was deleted successfully while the non-empty S3 bucket was protected.
- Manually delete all objects from the S3 bucket.
- Retry the stack deletion until it reaches `DELETE_COMPLETE`.

## 6) IAM / Security notes
- IAM resources require explicit acknowledgement during stack creation.
- IAM is treated as infrastructure in this context, not just identity.
- Resources like IAM roles with no runtime state or data are deleted cleanly by the stack, unlike data-bearing resources.

## 7) Common errors & fixes
- **Error:** S3 bucket deletion fails during stack removal, and the stack status becomes `DELETE_FAILED`.
  **Cause:** The S3 bucket is not empty. AWS protects data by default, and CloudFormation cannot delete a bucket containing user data.
  **Fix:** Manually delete all objects inside the S3 bucket and then retry the stack deletion.

## 8) Mini interview points

* **Stack Integrity & Drift:** Manual changes—such as deleting a resource from the console without using CloudFormation—cause "stack drift". Often, if an error occurs during initial creation or if a resource is deleted "out-of-band," the only reliable way to restore the correct ownership model and synchronization is to delete and recreate the stack entirely.
* **Why Deletion Fails:** Deletion failure is a safety signal, not an error. It indicates that AWS is protecting data (like a non-empty S3 bucket) or that manual intervention is required to acknowledge destruction.
* **The Danger of Updates:** Updates are more dangerous than creation because changing immutable properties can silently force a "Delete + Create" (resource replacement), leading to potential data loss or downtime.
* **Stack Boundaries:** A stack boundary should answer the question: "If I delete this stack, what system capability disappears?" Decoupling resources with different lifecycles (e.g., long-lived data vs. disposable compute) into separate stacks prevents "deletion fear."
* **The Shift in Ownership:** The core takeaway is moving from managing individual resources to managing the systems that own them.