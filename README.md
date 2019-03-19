![Build Status](https://travis-ci.org/dyntopia/cloudie.svg?branch=master)


# About

`cloudie` is a command-line utility that interacts with various cloud
service providers.  It uses [libcloud][1] and supports a large number of
[providers][2].


# Installation

```sh
$ make install
```


# Configuration

```toml
[role]
# Optional
default = "name of the role to use if --role isn't specified"

[role.<name>]
# Required options
provider = "service provider (e.g. digitalocean or vultr)"
key = "API key"

# Optional, may be overridden with command-line arguments
image = 1 # ID
location = 2 # ID
size = 3 # ID
ssh-key = "<path to public key>"
user-data = "<path to user-data for cloud-init>"
```


# Usage

## To create a new server

```sh
$ cloudie compute create-node   \
    --role <name of the role>   \
    --name <name of the node>   \
    --image <id>                \
    --location <id>             \
    --size <id>                 \
    --ssh-key <path>            \
    --user-data <path>
```


## To delete a server

```sh
$ cloudie compute destroy-node  \
    --role <name of the role>   \
    --id <id>
```


## To import a public SSH key for use in `create-node`

```sh
$ cloudie compute import-key-pair   \
    --role <name of the role>       \
    --name <name of the key>        \
    --ssh-key <path>
```


## To delete a public SSH key

```sh
$ cloudie compute delete-key-pair   \
    --role <name of the role>       \
    --id <id>
```


## To list available SSH keys

```sh
$ cloudie compute list-key-pairs --role <name of the role>
```


## To list servers

```sh
$ cloudie compute list-nodes --role <name of the role>
```


## To list available images

```sh
$ cloudie compute list-images --role <name of the role>
```


## To list available sizes

```sh
$ cloudie compute list-sizes --role <name of the role>
```


## To list available locations

```sh
$ cloudie compute list-locations --role <name of the role>
```


[1]: https://libcloud.apache.org/
[2]: https://libcloud.readthedocs.io/en/latest/supported_providers.html
