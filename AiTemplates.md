# Code Security
```
Review this [LANGUAGE] code for [VULNERABILITY_TYPES]:
Context: [PURPOSE]
Code: [CODE_BLOCK]
Output format:
1. Vulnerabilities found (severity: critical/high/medium/low)
2. Affected lines
3. Remediation steps
4. Example secure code
```
## Log review
```
System Role: You are an expert SOC analyst investigating a potential security incident in a local network environment.

Task: Analyze the provided log data and generate a clear, structured incident summary based on the specified parameters.

Incident Parameters:

[INCIDENT_ID]: (e.g., INC-001)

[TARGET_ENVIRONMENT]: (e.g., Proxmox VM, OPNsense Firewall, Windows Server)

[TIME_WINDOW]: (e.g., 2026-04-16 14:00:00 to 15:30:00)

Raw Log Entries:

Plaintext
[INSERT_RAW_LOGS_HERE]
Analysis Requirements:

Executive Summary: Provide a 2-3 sentence overview of what occurred.

Attack Vector & Chronology: Map out the sequence of events using the [TIME_WINDOW].

Extracted Artifacts: Identify and list any suspicious [SOURCE_IP_ADDRESSES], [USER_ACCOUNTS], or [PROCESS_NAMES].

Risk Assessment: Rate the severity (Low/Medium/High/Critical) for this specific [TARGET_ENVIRONMENT] and explain your reasoning.

Remediation Steps: Suggest concrete actions to secure the machine, block the threat, and prevent lateral movement.

Output Constraints:

Format the final report as a [PREFERRED_FORMAT_E.G._MARKDOWN_REPORT_OR_JSON].

Keep descriptions technical, concise, and focused on verifiable facts from the logs. Avoid speculative assumptions.
```
