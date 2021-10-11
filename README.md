#  hoard 

> A command organizer utility tool to hoard all your precious commands 💎🐉

![Example usage](img/hoard_example.gif)

#### What is a command organizer?

A command organizer lets you save commands that you often use, but are too complicated to remember.
For every **hoarded** command, `hoard` saves

- name
- tags
- description
- namespace where it lives in
- the command itself

If you get lost in your massive command history, and can't find for example a specific `docker` command out of thousand `docker` commands you've already ran,
just **hoard** it. With a **name** and **description** it will be much easier to find again. When you look for that command again a month later, take a look at your **hoarded** commands.

`hoard` is **not** supposed to replace shell history finder like `fzf` `atuin` or similar utilities. It rather should be used in conjunction with them.

## :love_letter: Table of contents

- [📦 Install](#install)
- [🤸 Usage](#usage)
- [:zap: Shortcuts](#shortcuts)

<a name="install"/>

## 📦 Install

### From source

It's best to use [rustup](https://rustup.rs/) to get setup with a Rust
toolchain, then you can run:

```
cargo build --release
```

Find the binaries in `./target/release/hoard`
Move it to wherever you need it ( Like `/usr/local/bin/hoard` )

### Linux

Install `hoard` by running

```
./install.sh
```

If you are running `fish` shell

```
LATEST_RELEASE=0.1.8 ./install.fish
```

### Brew on MacOS
```
brew tap Hyde46/hoard
brew install hoard
```
### Install Shell plugin

Install `hoard` as a plugin to enable autocomplete.
Depending on your shell, run one of the following commands.
To keep it installed for your next shell session, add the `source` command with an absolute path to your `.bashrc` or copy-paste the plugins content to your `.bashrc`.

#### bash

```
source src/shell/hoard.bash
```

#### zsh

```
source src/shell/hoard.zsh
```

#### fish

```
source src/shell/hoard.fish
```
<a name="usage"/>
 🤸 Usage

#### Save a new command

```
hoard new
```

#### Delete a command

```
hoard remove <name>
```

#### Delete all commands in a namespace

```
hoard remove_namespace <namespace_name>
```

#### Edit a command

```
hoard edit <name>
```

#### Search through command trove

```
<Ctrl-h>
```

Or alternatively, if not installed as a plugin, the interactive search can still be performed, though without autocomplete. This assumes the user to copy the command by mouse from the UI

```
hoard list
```

#### Import other trove files from `trove.yml` or urls pointing to a trove.yml file

```
hoard import /path/to/trove.yml
```
or
```
hoard import https://troves.com/new_trove.yml
```

#### Export trove file
```
hoard export /path/to/exported/trove.yml
```

<a name="shortcuts"/>

## :zap: Hoard list shortcuts 

Next item in command list

```
<Ctrl-N> / <Down-Arrow>
```

Previous item in command list

```
<Ctrl-P> / <Ctrl-Y> / <Up-Arrow>
```

Next namespace tab

```
<Ctrl-L> / <Right-Arrow>
```

Previous namespace tab

```
<Ctrl-H> / <Left-Arrow>
```

Select command

```
<Enter>
```

Quit

```
<Esc> / <Ctrl-D> / <Ctrl-C> / <Ctrl-G>
```
