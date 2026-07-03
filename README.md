This project takes advantage of Odoo's JSON logging configuration, providing an easy way to add metadata to logs using custom formatters and filters.

This project provides a filter to add git information to the logs, and a viewer to display the logs in a web page.

The viewer (`index.html`) was fully AI-generated and was not yet reviewed nor reworked but was tested in depth.

Alternative options like lnav, Logdy, etc. could most likely provide similar functionality, or even better filtering capabilities, but this viewer exists to match specific needs: the Odoo `RUNBOT` level, VS Code deep links, per-pid automatic filtering, ...

# Create a log config file

It is advised to put the config in `~/.config/Odoo/log_config.json`, matching the example given here.

```json
{
  "version": 1,
  "keep_odoo_default": true,
  "filters": {
    "git": {
      "()": "local_logging.git_context.GitFilter"
    }
  },
  "formatters": {
    "json": { "()": "odoo.logging.JSONFormatter" }
  },
  "handlers": {
    "json": {
      "class": "logging.handlers.WatchedFileHandler",
      "formatter": "json",
      "filename": "/home/{$USER}/logs/odoo_log.json",
      "level": "INFO",
      "filters": ["git"]
    }
  },
  "root": { "handlers": ["json"] }
}
```

Replace the literal text `{$USER}` with your username — this file has no variable substitution, so it needs to be edited by hand. Also confirm `local_logging.git_context.GitFilter` matches the actual module path and class name of your git filter (adjust if your filter file or class is named differently).

Make sure the logs directory exists and is writable by the Odoo user:

```
mkdir -p /home/$USER/logs
```

# Add the log config to the Odoo conf

Depending on the version, the config file could be in one of a few locations.

The current official location is `~/.config/Odoo/odoo.conf`, but `~/.odoorc` is commonly used for more recent versions.

It's advised to keep the file at `~/.config/Odoo/odoo.conf` and create a symlink to it at `~/.odoorc`:

```
ln -s ~/.config/Odoo/odoo.conf ~/.odoorc
```

Then add this line to the `[options]` section of `odoo.conf`:

```ini
[options]
...
log_config = ~/.config/Odoo/log_config.json
...
```

# Create the nginx config

Add this to `/etc/nginx/sites-enabled/logs`:

```nginx
server {
    listen 127.0.0.1:8111;

    # Serves the viewer (index.html, manifest.json, icons)
    root /home/{user}/src/local_logging/viewer;

    location / {
        try_files $uri $uri/ =404;
    }
    location /api/files/ {
        alias /home/{user}/logs/;
        autoindex on;
        autoindex_format json;
    }

    location ~ \.json$ {
        root /home/{user}/logs;
        default_type application/json;
        gzip off;
    }
}
```

and reload nginx
`sudo systemctl reload nginx`

# QOL: Allow Chrome to open vscode:// links without asking

Create `/etc/opt/chrome/policies/managed/vscode_autolaunch.json`:

```json
{
  "AutoLaunchProtocolsFromOrigins": [
    {
      "protocol": "vscode",
      "allowed_origins": [
        "https://runbot.odoo.com",
        "http://logs"
      ]
    }
  ]
}
```

# Optional: use a custom hostname

## Modify the nginx config

```nginx
listen       127.0.0.1:80;
server_name  logs;
```

Note that moving to port 80 means the port disappears from the URL — you'll browse to `http://logs/` instead of `http://logs:8111/`.
`server_name` is only needed to distinguish this server from others that may be running on the same port.

## Create the custom hostname

Add `logs` to `/etc/hosts`:

```
echo "127.0.0.1 logs" | sudo tee -a /etc/hosts
```

# Hide the "not secure" warning for this page

1. Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`.
2. Set it to **Enabled**.
3. In the text box that appears, enter the exact origin(s), e.g. `http://logs` — comma-separate multiple if needed.
4. Click **Relaunch** at the bottom.