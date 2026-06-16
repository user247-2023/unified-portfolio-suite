/**
 * Demo incident data.
 *
 * Purpose: Let the dashboard render a realistic, populated view WITHOUT a running
 * ingestion backend (useful for screenshots, design, and offline review). The
 * shape matches the ingestion API's `/incidents` response exactly, so swapping
 * to live data changes nothing in the UI.
 *
 * The first incident mirrors `seed_demo.py` (successful brute force, P1/95).
 */
export const DEMO_INCIDENTS = [
  {
    id: "inc_demo_p1",
    priority: "P1",
    risk_score: 95,
    entities: ["45.9.148.99"],
    alert_rules: ["brute_force", "successful_brute_force"],
    recommended_actions: [
      "Treat the affected account as compromised: reset credentials, revoke sessions/tokens.",
      "Isolate the affected host pending investigation.",
      "Hunt for lateral movement and persistence from the entity/host.",
      "Preserve logs for forensics before remediation.",
    ],
    rationale: [
      "entity=45.9.148.99",
      "+50 base from highest severity (CRITICAL).",
      "+5 for 2 correlated alerts.",
      "+15 external source IP involved.",
      "+15 sensitive account targeted.",
      "+10 multiple distinct detections (brute_force, successful_brute_force).",
      "= final risk score 95/100.",
      "priority=P1 (auto-escalate at 80)",
    ],
  },
  {
    id: "inc_demo_p2",
    priority: "P2",
    risk_score: 65,
    entities: ["203.0.113.7"],
    alert_rules: ["port_scan"],
    recommended_actions: [
      "Verify which scanned services are actually exposed and whether they should be.",
      "Block or rate-limit the scanning source at the firewall (after review).",
      "Confirm exposed services are patched and access-controlled.",
    ],
    rationale: [
      "entity=203.0.113.7",
      "+35 base from highest severity (HIGH).",
      "+15 external source IP involved.",
      "+15 sensitive account targeted.",
      "= final risk score 65/100.",
      "priority=P2",
    ],
  },
  {
    id: "inc_demo_p3",
    priority: "P3",
    risk_score: 45,
    entities: ["10.0.4.21"],
    alert_rules: ["brute_force"],
    recommended_actions: [
      "Review the source IP's reputation and recent history.",
      "Confirm the targeted account(s) are not compromised; enforce MFA.",
    ],
    rationale: [
      "entity=10.0.4.21",
      "+35 base from highest severity (HIGH).",
      "+10 internal repeat offender.",
      "= final risk score 45/100.",
      "priority=P3",
    ],
  },
];
