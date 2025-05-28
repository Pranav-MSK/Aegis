## Manage Alert Rules

`system/alerts/rules`

if rules are update, prometheus docker needs to be restarted. it's not possible to update rules without restarting the docker container.
within the update rule call the update function of the alert rule.
