# Week 6 – Stateful Serverless Job Controller

## 1) What this teaches 
- **Control-plane vs. Workload:** Understanding that deciding *if* work happens is often more critical than the work itself.
- **Stateful Statelessness:** How to implement persistence and coordination in a naturally stateless Lambda environment.
- **Atomic Locking:** Using DynamoDB as a single source of truth for concurrency control.
- **Idempotency by Design:** Enforcing execution rules at the data layer to prevent duplicate runs and race conditions.
- **Clarity through Layering:** Separating control logic (behavior) from business logic (output).

## 2) Goal
Implement a state-driven serverless job controller using DynamoDB and EventBridge to handle duplicate runs, retries, and rate limiting deterministically.

## 3) Architecture / Flow 
1. **Trigger:** EventBridge Scheduler invokes the Lambda every hour.
2. **Read:** Lambda fetches the current system state (status, version) from DynamoDB.
3. **Gate:** Logic exits if the job is already `RUNNING` or within a cooldown period.
4. **Lock:** Lambda performs an atomic update to set status to `RUNNING` using optimistic locking.
5. **Execute:** A placeholder workload is performed.
6. **Commit:** Lambda updates state to `IDLE`, increments success count, and sets the next allowed run time.

## 4) AWS Services + Why they were used
- **EventBridge Scheduler:** To trigger the job on a fixed schedule without manual intervention.
- **AWS Lambda:** Serves as the stateless executor for the control and workload logic.
- **DynamoDB:** Acts as the "Brain" and single source of truth for behavioral state and atomic locking.
- **CloudWatch Logs:** Used for debugging and visibility, though the system logic remains independent of them.

## 5) Recreation Guide 
### Setup
- [ ] Create a DynamoDB table named `job_control` with `PK` (Partition Key) and `SK` (Sort Key).
- [ ] Initialize the control item with `PK: JOB#hourly_processor`, `SK: STATE`, and `status: IDLE`.
- [ ] Create an EventBridge Schedule set to the desired frequency (e.g., cron hourly).

### Execution
- [ ] Implement `GetItem` logic to evaluate `next_allowed_run` and `status`.
- [ ] Implement `UpdateItem` with a `ConditionExpression` to ensure `status == IDLE` and `version` matches (Optimistic Locking).
- [ ] Ensure the Lambda exits immediately if gate conditions are not met to save costs.

### Verification (Proof checks)
- [ ] Inspect the `job_control` table to verify `run_count` increments correctly.
- [ ] Confirm `last_success_ts` and `next_allowed_run` are updated post-execution.
- [ ] Verify `last_error` is populated and `status` returns to `IDLE` upon failure.

### Cleanup
- [ ] Delete the EventBridge Schedule to stop recurring costs.
- [ ] Delete the DynamoDB table and Lambda function.

## 6) IAM / Security notes
- **Least Privilege:** The Lambda execution role requires `dynamodb:GetItem` and `dynamodb:UpdateItem` permissions scoped strictly to the `job_control` table.
- **State-Driven Observability:** The system is designed to be observable via DynamoDB state, reducing reliance on log searching for health checks.
- **Atomic Updates:** Conditional updates prevent race conditions and duplicate work when multiple triggers occur.

## 7) Common errors & fixes
- **Error:** Duplicate execution or race conditions.
  **Cause:** Concurrent Lambda invocations triggering before the first one sets the state.
  **Fix:** Use atomic conditional updates in DynamoDB (`status == IDLE`) to gate execution.
- **Error:** Stale or unclear state after a crash.
  **Cause:** Relying on memory-based state in a stateless runtime.
  **Fix:** Persist every state transition explicitly in DynamoDB so behavior remains deterministic after recovery.
- **Error:** Unexpected retries causing duplication.
  **Cause:** Default retry behavior in delivery mechanisms like EventBridge.
  **Fix:** Disable retries in the scheduler and control them via state-driven cooldowns in logic.

## 8) Key commands / snippets
```python
# DynamoDB Atomic Lock Update
table.update_item(
    Key={'PK': 'JOB#hourly_processor', 'SK': 'STATE'},
    UpdateExpression="SET #s = :r, last_run_ts = :now",
    ConditionExpression="#s = :i AND version = :v",
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={
        ':r': 'RUNNING',
        ':i': 'IDLE',
        ':now': current_time,
        ':v': expected_version
    }
)

```

## 9) Mini interview points   

### Stateless vs. Stateful

| Aspect | Stateless | Stateful |
| --- | --- | --- |
| **Definition** | Does not remember past executions | Remembers past events explicitly |
| **Memory** | Exists only during execution | Persisted beyond execution |
| **Failure impact** | State is lost on crash | State survives crashes |
| **Retry behavior** | Unsafe by default | Safe when designed correctly |
| **Concurrency** | Hard to control | Controlled via locks / versions |
| **Scaling** | Easy, horizontal | Requires coordination |
| **Source of truth** | None | External store (DB, cache, etc.) |
| **Typical AWS services** | Lambda, EventBridge | DynamoDB, RDS, S3 |
| **Cost model** | Pay per execution | Pay for storage + ops |
| **Debugging** | Logs only | State + logs |
| **Idempotency** | Must be engineered externally | Enforced via stored state |
| **Example in this week** | Lambda function | DynamoDB `job_control` table |
| **What can go wrong** | Duplicate work, race conditions | Stale state if badly designed |
| **When to use** | Pure computation, transformations | Coordination, scheduling, control |

Lambda is stateless (compute only), while DynamoDB provides the stateful authority needed for coordination.

* **Mindset:** "Design behavior first. Add work later." If the control plane is correct, business logic can be added safely.
* **Why not a while loop?** Loops hide state in memory. Persisted state ensures the system is deterministic and self-healing across invocations.
* **Efficiency:** A system that checks state and exits quickly without performing redundant work is a success, not a failure.
* **Atomic Coordination:** DynamoDB is the correct authority for behavior because it survives crashes and remains consistent across independent invocations.