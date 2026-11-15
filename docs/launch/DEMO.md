# Launch demo transcript

The exact output of `bash scripts/launch_demo.sh` (offline; the checked-in demo is copied to a temp
directory first, so nothing in this repository is modified).

```text
Acme Payments 2.0 renamed 'amount' to 'amount_cents'.

1) Find every affected call site
renamed #/components/schemas/Charge/properties: amount -> amount_cents
acme/billing.py:7:34  keyword  amount

1 change, 1 certain site, 0 ambiguity groups

2) Rewrite the call site and prove the change
renamed #/components/schemas/Charge/properties: amount -> amount_cents
--- a/acme/billing.py
+++ b/acme/billing.py
@@ -4,4 +4,4 @@
 
 
 def create_charge(amount):
-    return client.charges.create(amount=amount, currency="usd")
+    return client.charges.create(amount_cents=amount, currency="usd")
Proof: TESTS_PASSED
TESTS: python3 -c import acme.billing
Baseline exit: 0
After exit: 0
Skipped: none

1 change, 1 proposal, 1 passed, 0 characterized, 0 replayed, 0 build-only, 0 unverified, 0 PRs opened, 0 PRs refused

3) The same migration as a provider bundle (no PR)
provider: acme
migration: amount-cents

renamed #/components/schemas/Charge/properties: amount -> amount_cents
--- a/acme/billing.py
+++ b/acme/billing.py
@@ -4,4 +4,4 @@
 
 
 def create_charge(amount):
-    return client.charges.create(amount=amount, currency="usd")
+    return client.charges.create(amount_cents=amount, currency="usd")
Proof: TESTS_PASSED
TESTS: python3 -c import acme.billing
Baseline exit: 0
After exit: 0
Skipped: none

1 change, 1 proposal, 1 passed, 0 characterized, 0 replayed, 0 build-only, 0 unverified, 0 PRs opened, 0 PRs refused
```

What to point at in a launch post: one certain site, the exact rename, `Proof: TESTS_PASSED`, and
the provider-bundle path that a vendor can run without opening a PR.
