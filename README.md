# Q Org

Adds **Enhanced General Ledger**. The Python report directly executes ERPNext General Ledger and only enriches presentation data.

## Install

```bash
cd ~/frappe-bench
bench get-app https://github.com/SalahAddinAbdo/qorg.git
bench --site YOUR-SITE install-app qorg
bench execute qorg.scripts.sync_general_ledger.sync
bench build --app qorg
bench --site YOUR-SITE migrate
bench --site YOUR-SITE clear-cache
bench restart
```

Run the sync command after every ERPNext upgrade, then commit the regenerated JS/HTML if Git is the source of truth.
