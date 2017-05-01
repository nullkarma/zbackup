# Backups with rsync and zfs

This is a very simple approach to backup a hosts filesystem with rync
and dumping it into a zfs filesystem / snapshot.

## Configuration

### default

Global definition of rsync parameters and more.

```yaml

default:
  logdir: /var/log/zbackup
  rotate: 6
  snapname: "%d-%m-%Y-%X"
  rsync_user: root
  rsync_path: /
  rsync_args:
    - archive
    - numeric-ids
    - hard-links
    - compress
    - delete-after
    - delete-excluded
    - inplace
    - rsync-path='ionice -c 3 nice -n 20 rsync'
    - bwlimit=40960
  exclude:
    - var/log/*
    - var/cache/*
    - var/spool/*
    - var/tmp/*
    - var/run/*
    - tmp/*
    - proc/*
    - ...
```
### conf.d

Configuration files can also be placed inside the `conf.d` directory. The filename must match the zfs filesystem name.

#### conf.d/host.example.com.yaml

```yaml
backup/hosts/host.example.com:
    config:
        rotate: 1
        exclude:
            - foo/bar/*
```

### zfs filesystem config (zfc)

A zfs filesystem config is defined by its equivalent found in `zfs list` and is broken into two pieces:

```yaml
backup/hosts/frontend01.production.example.com:
    config:
    plans:
```

Default parameters can be overridden by defining the `config` section inside
the zfc definition.

#### Note

- `include` and `exclude` will be appended
- `rsync_args` will be overridden.

```yaml
backup/hosts/frontend01.production.example.com:
    config:
        rotate: 10
        exclude:
            - foo/bar/*
        include:
            - bar/baz/*
```

`rotate` would be overridden, but `foo/bar/*` would be appended to list of
default excludes from the default config definition.

#### Inheritance

If your defined zfc is a parent filesystem like `backup/hosts` in the example above,
the `config` parameters will be applied to every child filesystem.
However, they can be overriden by a child zfc definition (`backup/hosts/frontend01.production.example.com`)
or by defining plans.

#### Working with plans

Another way of defining a more granular ruleset of rsync in-/ and excludes, args etc.,
plans can be combined with inheritance.

Say you have a parent filesystem containing all your host filesystems called `backup/hosts`.
The config would be defined like:

```yaml

backup/hosts:
    config:
        rotate: 5
    exclude:
        - some/dir/*
    include:
        - foo/bar/*
    plans:
```

Every child would inherit its parent config, excludes and includes.
A plan can match a pattern and apply special configs to a single or a group of filesystems.
Your postgresql databases should have a `rotation` of `10`,
exclude the `/var/lib/postgresql` directory and inherit all other parameters from its parent.

```yaml

backup/hosts:
    config:
        rotate: 5
    exclude:
        - some/dir/*
    include:
        - foo/bar/*
    plans:
        -
            match: "^db[0-9]+.(prod|stage).example.com$"
            config:
                rotate: 10
                exclude:
                    - var/lib/postgresql/*
```

Regex Pattern can only be used within a `plan` context. But not at zfc level.

```
backup/hosts/^db[0-9]+.example.org$: # BAD
```

The merge rules for `config` parameters from the zfc definition level also apply to plans.
In this example, `exclude` would contain `some/dir/*` and `var/lib/postgresql/*`.
Inherited parameters can be completely overridden/ignored by passing the `plan` parameter to a plan.
If `plan` is given, `config` will is omitted in case of a match.

```yaml
plans:
    -
        match: "^db[0-9]+.(prod|stage).example.com$"
        plan: /etc/zbackup/plans/databases.yaml
```

The config (inheritance) priority is:

```default < zfc parent < plan config < plan file < zfc child < conf.d```

```yaml

backup/hosts:
    config:
        rotate: 5
    exclude:
        - some/dir/*
    include:
        - foo/bar/*
    plans:
        -
            match: "^db[0-9]+.(prod|stage).example.com$"
            plan: /etc/zbackup/plans/database.yaml

backup/hosts/db01.prod.example.com:
    config:
        rotate: 1

```

`backup/hosts/db01.prod.example.com` ignores `plan` config and overrides default config.